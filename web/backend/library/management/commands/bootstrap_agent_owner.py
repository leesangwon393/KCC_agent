"""Create the initial web login and Mac bridge token once."""
import hashlib
import json
import secrets
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from library.models import AgentLink


class Command(BaseCommand):
    help = "Create a new non-admin owner account and Mac bridge token"

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, username, **_options):
        users = get_user_model()
        if users.objects.filter(username=username).exists():
            raise CommandError("User already exists; use issue_agent_token to rotate bridge access")
        password = secrets.token_urlsafe(32)
        token = secrets.token_urlsafe(48)
        owner = users.objects.create_user(username=username, password=password)
        AgentLink.objects.create(owner=owner, label="Mac agent", token_hash=hashlib.sha256(token.encode()).hexdigest())
        self.stdout.write(json.dumps({"username": username, "password": password, "bridge_token": token}))
