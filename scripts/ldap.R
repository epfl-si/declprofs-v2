############################################################
# LDAP search via Python (reticulate)
# Equivalent of the provided Python function
############################################################

# ---- Configuration ----

LDAP_HOST    <- "ldap.epfl.ch"   # adapter si nécessaire
LDAP_PORT    <- 389              # 636 si LDAPS
LDAP_BASE_DN <- "o=epfl,c=ch"    # adapter si nécessaire

# ---- Load reticulate ----

if (!requireNamespace("reticulate", quietly = TRUE)) {
  install.packages("reticulate")
}

library(reticulate)

use_python("/home/duratti/.pyenv/versions/3.14.4/envs/declprofs-django/bin/python", required = TRUE)

# ---- Vérifier que python-ldap est dispo ----

if (!py_module_available("ldap")) {
  stop("Le module Python 'ldap' n'est pas installé.\nInstalle-le avec: pip install python-ldap")
}

ldap <- import("ldap")

ldap_search <- function(sciper = NULL, email = NULL,
                        host = "ldap.epfl.ch",
                        port = 389,
                        base_dn = "o=epfl,c=ch") {

  if (is.null(sciper) && is.null(email)) {
    stop("Provide either sciper or email")
  }

  epfl_ldap <- ldap$initialize(sprintf("ldap://%s:%d", host, as.integer(port)))

  search_filter <- "(&(objectClass=EPFLorganizationalPerson)"
  if (!is.null(sciper)) {
    search_filter <- paste0(search_filter, "(uniqueIdentifier=", sciper, "))")
  } else {
    search_filter <- paste0(search_filter, "(mail=", email, "))")
  }

  # On demande TOUS les attributs
  ldap_user_list <- epfl_ldap$search_ext_s(
    base_dn,
    ldap$SCOPE_SUBTREE,
    search_filter,
    NULL
  )

  if (length(ldap_user_list) == 0) return(NULL)

  # Prendre la première entrée valide
  ldap_user <- ldap_user_list[[1]]
  attrs <- ldap_user[[2]]

  # Helper pour décoder raw → string
  decode_ldap <- function(x) {
    if (inherits(x, "raw")) return(rawToChar(x))
    as.character(x)
  }

  # Extraction sécurisée
  get_attr <- function(attr) {
    if (attr %in% names(attrs)) {
      return(decode_ldap(attrs[[attr]][[1]]))
    }
    NULL
  }

  sciper_val <- get_attr("uniqueIdentifier")
  email_val <- get_attr("mail")
  username_val <- get_attr("uid")
  lastname_val <- get_attr("sn")
  firstname_val <- get_attr("givenName")

  list(
    sciper    = sciper_val,
    email     = email_val,
    username  = username_val,
    lastname  = lastname_val,
    firstname = firstname_val
  )
}

result <- ldap_search(sciper = "183631")
print(result)

############################################################
