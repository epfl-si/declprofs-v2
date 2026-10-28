############################################################
# Migration MariaDB -> PostgreSQL / Django
# avec enrichissement LDAP
############################################################

library(DBI)
library(RMariaDB)
library(RPostgres)
library(dplyr)
library(yaml)
library(httr2)

# ----------------------------------------------------------
# Charger la fonction LDAP
# ----------------------------------------------------------

source("ldap.R")

# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------

is_simulation <- FALSE
environment <- "prod"

maria_conf <- yaml::read_yaml(paste0("/keybase/team/epfl_declprofs/secrets-", environment, ".yml"))
pg_conf <- yaml::read_yaml("/keybase/team/epfl_declprofs/secrets.yml")

users_table <- "users_user"
useryear_table <- "users_useryear"
activities_table <- "activities_activity"

# ----------------------------------------------------------
# ConnexionS bases de données
# ----------------------------------------------------------

con_maria <- dbConnect(
  RMariaDB::MariaDB(),
  host     = maria_conf$db$host,
  dbname   = "declprofs",
  user     = maria_conf$db$user,
  password = maria_conf$db$password,
  port     = 3306
)

con_pg <- dbConnect(
  RPostgres::Postgres(),
  host     = pg_conf[[environment]]$postgres$host,
  dbname   = pg_conf[[environment]]$postgres$name,
  port     = pg_conf[[environment]]$postgres$port,
  user     = pg_conf[[environment]]$postgres$user,
  password = pg_conf[[environment]]$postgres$password,
)

on.exit({
  if (dbIsValid(con_maria)) dbDisconnect(con_maria)
}, add = TRUE)

on.exit({
  if (dbIsValid(con_pg)) dbDisconnect(con_pg)
}, add = TRUE)

# ----------------------------------------------------------
# Charger les activités MariaDB
# ----------------------------------------------------------

profsacts_data <- dbGetQuery(
  con_maria,
  "
  SELECT
    persid,
    year,
    activity,
    principal,
    dateFrom,
    dateTo,
    ts
  FROM profsacts
  WHERE year IN (2025, 2026)
  "
) |>
  mutate(
    persid = as.character(persid),
    year = as.integer(year)
  )

cat(
  "Nombre de lignes Maria :",
  nrow(profsacts_data),
  "\n"
)

# ----------------------------------------------------------
# Charger les remarques
# ----------------------------------------------------------

remarks_data <- dbGetQuery(
  con_maria,
  "
  SELECT
    year,
    persid,
    remark,
    prof_remark
  FROM remarks
  WHERE year IN (2025, 2026)
  "
) |>
  mutate(
    persid = as.character(persid),
    year = as.integer(year)
  )

cat(
  "Nombre de remarques Maria :",
  nrow(remarks_data),
  "\n"
)

# ----------------------------------------------------------
# Construire les utilisateurs via LDAP
# ----------------------------------------------------------

get_user_unit <- function(sciper) {

  url <- paste0(
    "https://api.epfl.ch/v1/accreds?persid=",
    sciper
  )

  response <- request(url) |>
    req_auth_basic(
      username = pg_conf[[environment]]$epfl_service$name,
      password = pg_conf[[environment]]$epfl_service$password
    ) |>
    req_headers(
      Accept = "application/json"
    ) |>
    req_perform()

  data <- resp_body_json(response)

  accreds <- data$accreds

  if (is.null(accreds)) {
    return("")
  }

  for (accred in accreds) {

    person <- accred$person

    if (is.null(person)) {
      next
    }

    email <- person$email
    order <- accred$order

    if (
      !is.null(email) &&
      nzchar(as.character(email)) &&
      !is.null(order) &&
      as.integer(order) == 1
    ) {

      unit <- accred$unit

      if (
        !is.null(unit) &&
        !is.null(unit$path)
      ) {
        return(as.character(unit$path))
      }

      return("")
    }
  }

  ""
}

unique_users <- unique(
  as.character(profsacts_data$persid)
)

users_list <- lapply(
  unique_users,
  function(pid) {

    cat("LDAP lookup :", pid, "\n")

    ldap_info <- ldap_search(sciper = pid)

    if (is.null(ldap_info)) {
      return(NULL)
    }

    unit <- tryCatch(
      get_user_unit(pid),
      error = function(e) {
        cat(
          "Erreur récupération unité pour",
          pid,
          ":",
          conditionMessage(e),
          "\n"
        )
        ""
      }
    )
    data.frame(
      username   = as.character(ldap_info$username),
      email      = as.character(ldap_info$email),
      first_name = ldap_info$firstname,
      last_name  = ldap_info$lastname,
      sciper     = pid,
      unit       = unit,
      has_access = TRUE
    )
  }
)

users_list <- Filter(
  Negate(is.null),
  users_list
)

if (length(users_list) == 0) {
  stop("Aucun utilisateur LDAP trouvé")
}

users_df <- do.call(
  rbind,
  users_list
)

# Éviter les doublons éventuels
users_df <- users_df |>
  distinct(sciper, .keep_all = TRUE)

# Compléter les champs de AbstractUser
# L'authentification est gérée par Entra ID :
# le mot de passe Django est donc inutilisable.
users_df <- users_df |>
  mutate(
    password = "!",
    last_login = as.POSIXct(NA),
    is_superuser = FALSE,
    is_staff = FALSE,
    is_active = TRUE,
    date_joined = Sys.time()
  )

cat(
  "Nombre Users LDAP trouvés :",
  nrow(users_df),
  "\n"
)

# ----------------------------------------------------------
# Fonction robuste pour les dates
# ----------------------------------------------------------

safe_date <- function(
  x,
  fallback_year = NULL,
  is_start = TRUE
) {

  x <- as.character(x)
  x <- trimws(x)

  # Valeurs considérées comme absentes
  invalid <- is.na(x) |
    x == "" |
    x == "0000-00-00" |
    x == "NULL" |
    x == "NA"

  x[invalid] <- NA_character_

  # Conversion explicite uniquement
  d <- as.Date(
    x,
    format = "%Y-%m-%d"
  )

  # Fallback sur l'année si nécessaire
  if (!is.null(fallback_year)) {

    missing <- is.na(d) &
      !is.na(fallback_year)

    if (is_start) {

      d[missing] <- as.Date(
        paste0(
          fallback_year[missing],
          "-01-01"
        ),
        format = "%Y-%m-%d"
      )

    } else {

      d[missing] <- as.Date(
        paste0(
          fallback_year[missing],
          "-12-31"
        ),
        format = "%Y-%m-%d"
      )
    }
  }

  d
}

# ----------------------------------------------------------
# Transaction PostgreSQL
# ----------------------------------------------------------

if (!is_simulation) {
  dbBegin(con_pg)
}

tryCatch({

  # --------------------------------------------------------
  # Vider Activities
  #
  # Les utilisateurs sont supprimés ensuite.
  # CASCADE est nécessaire à cause de la ForeignKey.
  # --------------------------------------------------------

  if (is_simulation) {

    cat("\n--- SIMULATION ---\n")
    cat('TRUNCATE TABLE "Users", "UserYear", "Activities" RESTART IDENTITY CASCADE\n')

  } else {

    dbExecute(
      con_pg,
      sprintf(
        'TRUNCATE TABLE "%s", "%s", "%s" RESTART IDENTITY CASCADE',
        users_table,
        useryear_table,
        activities_table
      )
    )
  }

  # --------------------------------------------------------
  # Insérer les utilisateurs
  # --------------------------------------------------------

  if (is_simulation) {

    cat("\n--- SIMULATION : Users à insérer ---\n")

    print(users_df)

  } else {

    dbWriteTable(
      con_pg,
      users_table,
      users_df,
      append = TRUE,
      row.names = FALSE
    )
  }

  cat(
    "Users insérés dans PostgreSQL :",
    nrow(users_df),
    "\n"
  )

  # --------------------------------------------------------
  # Récupérer les IDs Django
  # --------------------------------------------------------

  if (is_simulation) {

    users_pg <- users_df |>
      mutate(id = row_number()) |>
      select(id, sciper)

  } else {

    users_pg <- dbGetQuery(
      con_pg,
      sprintf(
        'SELECT id, sciper FROM "%s"',
        users_table
      )
    )
  }

  # --------------------------------------------------------
  # Création des UserYear
  # --------------------------------------------------------

  years <- c(2025, 2026)

  useryears_final <- expand.grid(
    user_id = users_pg$id,
    year = years
  ) |>
    as.data.frame() |>
    mutate(
      is_eligible = FALSE,
      is_exempted = FALSE,
      is_employed = TRUE,
      updated_at = as.POSIXct(NA),
      reminder_at = as.POSIXct(NA),
      draft_count = 0L,
      missing_count = 1L,
      submitted_count = 0L
    )

  # --------------------------------------------------------
  # Associer les activités aux utilisateurs
  # --------------------------------------------------------

  activities_df <- profsacts_data |>
    mutate(
      persid = as.character(persid)
    ) |>
    inner_join(
      users_pg,
      by = c("persid" = "sciper")
    )

  cat(
    "Activités avec utilisateur trouvé :",
    nrow(activities_df),
    "\n"
  )

  # --------------------------------------------------------
  # Mise à jour des UserYear
  # --------------------------------------------------------

  # Nombre de submits par UserYear
  activity_counts <- activities_df |>
    count(
      user_id = id,
      year,
      name = "activity_count"
    )

  useryears_final <- useryears_final |>
    left_join(
      activity_counts,
      by = c("user_id", "year")
    ) |>
    mutate(
      submitted_count = coalesce(activity_count, 0L),
      missing_count = if_else(submitted_count > 0L, 0L, 1L)
    ) |>
    select(
      -activity_count
    )

  print(useryears_final)

  # --------------------------------------------------------
  # Ajouter les remarques
  # --------------------------------------------------------

  activities_df <- activities_df |>
    left_join(
      remarks_data,
      by = c("persid", "year")
    )

  # --------------------------------------------------------
  # Convertir les dates
  # --------------------------------------------------------

  cat("\n--- DEBUG DATES ---\n")

  print(
    activities_df |>
      select(
        persid,
        year,
        dateFrom,
        dateTo
      )
  )

  activities_df$date_start <- safe_date(
    activities_df$dateFrom,
    activities_df$year,
    is_start = TRUE
  )

  activities_df$date_end <- safe_date(
    activities_df$dateTo,
    activities_df$year,
    is_start = FALSE
  )

  # --------------------------------------------------------
  # Construire les données Activities
  # --------------------------------------------------------

  activities_final <- data.frame(
    status       = "submitted",
    user_id      = activities_df$id,
    activity     = activities_df$activity,
    principal    = activities_df$principal,
    comments     = activities_df$prof_remark,
    comments_apr = activities_df$remark,
    date_start   = activities_df$date_start,
    date_end     = activities_df$date_end
  )

  # Gérer les NA dans les commentaires
  activities_final$comments[
    is.na(activities_final$comments)
  ] <- ""

  activities_final$comments_apr[
    is.na(activities_final$comments_apr)
  ] <- ""

  cat(
    "Nombre Activities à insérer :",
    nrow(activities_final),
    "\n"
  )

  # --------------------------------------------------------
  # Insérer UserYear
  # --------------------------------------------------------

  if (is_simulation) {

    cat("\n--- SIMULATION : UserYear à insérer ---\n")

    print(useryears_final)

  } else {

    dbWriteTable(
      con_pg,
      useryear_table,
      useryears_final,
      append = TRUE,
      row.names = FALSE
    )
  }

  cat(
    "UserYear insérés dans PostgreSQL :",
    nrow(useryears_final),
    "\n"
  )

  # --------------------------------------------------------
  # Insérer Activities par chunks
  # --------------------------------------------------------

  chunk_size <- 500

  if (nrow(activities_final) > 0) {

    for (
      i in seq(
        1,
        nrow(activities_final),
        by = chunk_size
      )
    ) {

      end <- min(
        i + chunk_size - 1,
        nrow(activities_final)
      )

      chunk <- activities_final[
        i:end,
        ,
        drop = FALSE
      ]

      cat(
        "Insertion Activities :",
        i,
        "-",
        end,
        "\n"
      )

      if (is_simulation) {

        cat(
          "\n--- SIMULATION : Activities",
          i,
          "-",
          end,
          "---\n"
        )

        #print(chunk)

      } else {

        dbWriteTable(
          con_pg,
          activities_table,
          chunk,
          append = TRUE,
          row.names = FALSE
        )
      }
    }
  }

  # --------------------------------------------------------
  # Commit
  # --------------------------------------------------------

  if (!is_simulation) {

    dbCommit(con_pg)

    cat("Transaction PostgreSQL commitée\n")

  } else {

    cat(
      "\n--- SIMULATION TERMINÉE ---\n",
      "Aucune donnée n'a été modifiée dans PostgreSQL.\n"
    )
  }

}, error = function(e) {

  if (!is_simulation) {
    dbRollback(con_pg)
  }
  cat(
    "ERREUR : transaction annulée\n",
    conditionMessage(e),
    "\n"
  )

  stop(e)
})

# ----------------------------------------------------------
# Vérification
# ----------------------------------------------------------

if (is_simulation) {

  cat("\n========== RÉSULTAT SIMULATION ==========\n")

  cat(
    "Users qui seraient insérés :",
    nrow(users_df),
    "\n"
  )

  cat(
    "Activities qui seraient insérées :",
    nrow(activities_final),
    "\n"
  )

  cat("\n--- Aperçu Users ---\n")

  print(head(users_df, 20))

  cat("\n--- Aperçu Activities ---\n")

  print(head(activities_final, 20))

  cat("\n🎉 Simulation terminée :", "aucune modification PostgreSQL.\n")

} else {

  count_users <- dbGetQuery(
    con_pg,
    'SELECT COUNT(*) AS n FROM "Users"'
  )

  count_useryears <- dbGetQuery(
    con_pg,
    'SELECT COUNT(*) AS n FROM "UserYear"'
  )

  count_activities <- dbGetQuery(
    con_pg,
    'SELECT COUNT(*) AS n FROM "Activities"'
  )

  cat("Users :", count_users$n, "\n")
  cat("UserYear :", count_useryears$n, "\n")
  cat("Activities :", count_activities$n, "\n")

  check <- dbGetQuery(
    con_pg,
    '
    SELECT
      COUNT(*) AS activities,
      COUNT(DISTINCT user_id) AS users
    FROM "Activities"
    '
  )

  print(check)

  check_user_year <- dbGetQuery(
    con_pg,
    '
    SELECT
      year,
      COUNT(*) AS useryears
    FROM "UserYear"
    GROUP BY year
    ORDER BY year
    '
  )

  print(check_user_year)

}

if (is_simulation) {

  cat("\n--- SIMULATION : vérification des Activities ---\n")

  activities_check <- activities_final |>
    left_join(
      users_pg,
      by = c("user_id" = "id")
    ) |>
    select(
      sciper,
      activity,
      principal,
      date_start,
      date_end,
      status
    ) |>
    arrange(date_start) |>
    head(20)

} else {

  activities_check <- dbGetQuery(
    con_pg,
    "
    SELECT
      a.id,
      u.sciper,
      a.activity,
      a.principal,
      a.date_start,
      a.date_end,
      a.status
    FROM activities_table a
    JOIN users_table u
      ON a.user_id = u.id
    ORDER BY a.date_start
    LIMIT 20
    "
  )

}

print(activities_check)

cat(
  "🎉 Migration MariaDB → PostgreSQL terminée avec succès\n"
)

if (dbIsValid(con_maria)) {
  dbDisconnect(con_maria)
}

if (dbIsValid(con_pg)) {
  dbDisconnect(con_pg)
}
