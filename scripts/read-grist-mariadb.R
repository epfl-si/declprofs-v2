############################################################
# Afficher toutes les tables MariaDB + leurs colonnes
############################################################

library(DBI)
library(RMariaDB)
library(yaml)

# ----------------------------------------------------------
# 1. Connexion MariaDB
# ----------------------------------------------------------
maria_conf <- yaml::read_yaml("/keybase/team/epfl_declprofs/secrets-test.yml")

con_maria <- dbConnect(
  RMariaDB::MariaDB(),
  host = maria_conf$db$host,
  user = maria_conf$db$user,
  password = maria_conf$db$password,
  dbname = "declprofs",
  port = 3306
)

# ----------------------------------------------------------
# 2. Lister les tables
# ----------------------------------------------------------
tables_maria <- dbListTables(con_maria)

cat("Nombre de tables trouvées :", length(tables_maria), "\n\n")

# ----------------------------------------------------------
# 3. Afficher colonnes pour chaque table
# ----------------------------------------------------------
for (tbl in tables_maria) {
  cat("====================================\n")
  cat("Table :", tbl, "\n")
  cat("------------------------------------\n")
  
  structure <- dbGetQuery(con_maria, paste0("DESCRIBE `", tbl, "`"))
  print(structure)
  cat("\n")
}

# ----------------------------------------------------------
# 4. Fermeture connexion
# ----------------------------------------------------------
dbDisconnect(con_maria)

cat("🔒 Connexion MariaDB fermée proprement\n")