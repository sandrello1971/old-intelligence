#!/usr/bin/env python3
import sys
sys.path.append('/app')

print("🚀 CRM COMPANIES & CONTACTS SYNC (FULL 100)")
print("⚡ Rate limit: 40 requests/minute respected")
print("=" * 50)

try:
    from integrations.crm_incloud.companies_contacts_sync import sync_companies_safe
    # Sync tutte le 100 aziende dal CRM
    result = sync_companies_safe(limit=100, dry_run=False)
    
    print("=" * 50)
    print("📊 CRM COMPANIES SYNC RESULTS (FULL)")
    print("=" * 50)
    for key, value in result.items():
        if key != 'fatal_error' or value:
            print(f"{key}: {value}")
    print("=" * 50)
    
    if result.get('fatal_error'):
        print(f"❌ Fatal Error: {result['fatal_error']}")
    else:
        print("✅ SYNC COMPLETED SUCCESSFULLY!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
