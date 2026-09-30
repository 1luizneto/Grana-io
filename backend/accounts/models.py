from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email=Usuario.normalizar_email(email))

    def _criar(self, email, nome, password, **extra):
        usuario = self.model(email=Usuario.normalizar_email(email), nome=nome.strip(), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, nome, password=None, **extra):
        # Contas comuns nunca recebem privilégios (FR-011).
        extra["is_staff"] = False
        extra["is_superuser"] = False
        return self._criar(email, nome, password, **extra)

    def create_superuser(self, email, nome, password=None, **extra):
        # Só pelo comando createsuperuser, fora do fluxo público de cadastro.
        extra["is_staff"] = True
        extra["is_superuser"] = True
        return self._criar(email, nome, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuário do Grana.io, identificado pelo e-mail (specs/002-cadastro-usuario/data-model.md)."""

    email = models.EmailField(max_length=254, unique=True)
    nome = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    def __str__(self):
        return self.email

    @staticmethod
    def normalizar_email(valor):
        """Único ponto de normalização do e-mail: sem espaços nas pontas e em minúsculas."""
        return valor.strip().lower()

    def save(self, *args, **kwargs):
        self.email = self.normalizar_email(self.email)
        self.nome = self.nome.strip()
        super().save(*args, **kwargs)
