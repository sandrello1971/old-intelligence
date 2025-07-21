"""CRM InCloud Integration Module"""
from .companies_contacts_sync import sync_companies_safe, sync_contacts_safe
__all__ = ["sync_companies_safe", "sync_contacts_safe"]
