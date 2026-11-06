"""Issue a Mac bridge token to an existing Django user."""
import hashlib
import secrets
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from library.models import AgentLink


class Command(BaseCommand):
    help = "Create or rotate a Mac bridge token for an existing user"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--label", default="Mac agent")

    def handle(self, username, label, **_options):
        owner = get_user_model().objects.filter(username=username).first()
        if owner is None:
            raise CommandError("User does not exist")
        token = secrets.token_urlsafe(48)
        link = AgentLink.objects.filter(owner=owner, label=label).first()
        if link is None:
            link = AgentLink(owner=owner, label=label)
        link.token_hash = hashlib.sha256(token.encode()).hexdigest()
        link.snapshot = {}
        link.last_seen_at = None
        link.save()
        link.commands.filter(status__in=["pending", "running"]).update(status="failed", result={"error": "Token rotated"})
        self.stdout.write(token)
