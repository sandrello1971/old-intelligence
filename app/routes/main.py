
# ✅ SERVICES TREE ROUTER  
try:
    from app.routes.services_tree import router as services_tree_router
    app.include_router(services_tree_router)
    print('✅ Services Tree caricato')
except Exception as e:
    print(f'❌ Errore services_tree: {e}')

