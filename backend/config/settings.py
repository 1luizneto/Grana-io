"""
Settings do Grana.io.

Toda configuração que varia por ambiente vem de variáveis de ambiente (12-factor).
Os valores padrão de desenvolvimento ficam no compose.yaml; aqui os padrões são seguros
(DEBUG desligado). Variáveis documentadas em specs/001-infra-docker/contracts/environment.md.
"""

from pathlib import Path

from config.env import CHAVE_DEV_PADRAO, env_bool, env_list, env_str, validar_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env_str("DJANGO_SECRET_KEY") or CHAVE_DEV_PADRAO
DEBUG = env_bool("DJANGO_DEBUG", False)
validar_secret_key(SECRET_KEY, DEBUG)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

# A própria interface chama a API pelo proxy do Vite (mesma origem), então nenhuma origem é
# liberada por padrão. Origens extras só por configuração (FR-013).
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "accounts",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_str("POSTGRES_DB", "grana"),
        "USER": env_str("POSTGRES_USER", "grana"),
        "PASSWORD": env_str("POSTGRES_PASSWORD"),
        "HOST": env_str("POSTGRES_HOST", "db"),
        "PORT": env_str("POSTGRES_PORT", "5432"),
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Usuário próprio, identificado pelo e-mail (specs/002-cadastro-usuario, research R-01).
AUTH_USER_MODEL = "accounts.Usuario"

REST_FRAMEWORK = {
    # A autenticação JWT entra na US-02; até lá nenhuma rota autentica.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    # Toda rota nasce protegida (RNF-02); rotas públicas declaram AllowAny explicitamente.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
