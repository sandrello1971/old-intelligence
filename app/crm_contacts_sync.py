#!/usr/bin/env python3
import sys
sys.path.append('/app')

print("👤 CRM CONTACTS SYNC TEST (10 contatti)")
print("⚡ Rate limit: 40 requests/minute respected")
print("=" * 50)

try:
    from integrations.crm_incloud.companies_contacts_sync import sync_contacts_safe
    # Test con 10 contatti per iniziare
    result = sync_contacts_safe(limit=10, dry_run=False)
    
    print("=" * 50)
    print("📊 CRM CONTACTS SYNC RESULTS")
    print("=" * 50)
    for key, value in result.items():
        if key != 'fatal_error' or value:
            print(f"{key}: {value}")
    print("=" * 50)
    
    if result.get('fatal_error'):
        print(f"❌ Fatal Error: {result['fatal_error']}")
    else:
        print("✅ CONTACTS SYNC TEST COMPLETED!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
