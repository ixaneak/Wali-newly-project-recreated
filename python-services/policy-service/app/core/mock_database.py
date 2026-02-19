from datetime import datetime
import uuid

# Global in-memory store
MOCK_DATA_STORE = {
    "Policy": []
}

class MockQuery:
    def __init__(self, model, items=None):
        self.model = model
        self.items = items if items is not None else MOCK_DATA_STORE.get(model.__name__, [])

    def filter(self, *expressions):
        # This is the tricky part. SQLAlchemy expressions are complex.
        # But for this specific demo, we can perform a little magic.
        # We know the PolicyService filters by:
        # 1. Policy.id == policy_id
        # 2. Policy.user_id == user_id
        # 3. Policy.status == status_filter
        
        filtered_items = list(self.items) # Copy!
        
        for expr in expressions:
            try:
                # SQLAlchemy BinaryExpression has .left (Column), .operator, .right (Value)
                # We can try to inspect it.
                if hasattr(expr, 'left') and hasattr(expr, 'right'):
                    column_name = expr.left.name
                    value = expr.right.value
                    
                    # Helper for UUID comparison
                    def safe_compare(a, b):
                        if isinstance(a, uuid.UUID) and isinstance(b, str):
                            return str(a) == b
                        if isinstance(a, str) and isinstance(b, uuid.UUID):
                            return a == str(b)
                        return a == b

                    # Perform filtering
                    filtered_items = [
                        item for item in filtered_items 
                        if safe_compare(getattr(item, column_name, None), value)
                    ]
                elif hasattr(expr, 'operator') and hasattr(expr, 'left'):
                     # Handle simple != check
                     if str(expr.operator) == 'operator.ne':
                          column_name = expr.left.name
                          value = expr.right.value
                          filtered_items = [
                               item for item in filtered_items
                               if getattr(item, column_name, None) != value
                          ]
            except Exception:
                pass
                
        return MockQuery(self.model, filtered_items)

    def filter_by(self, **kwargs):
        filtered = []
        for item in self.items:
            match = True
            for key, value in kwargs.items():
                if getattr(item, key, None) != value:
                    match = False
                    break
            if match:
                filtered.append(item)
        return MockQuery(self.model, filtered)

    def order_by(self, *args):
        # Simple sort by created_at desc if requested (PolicyService uses it)
        # We'll just assume desc sort on created_at for everything as a heuristic
        try:
             self.items.sort(key=lambda x: x.created_at, reverse=True)
        except:
             pass
        return self

    def offset(self, n):
        return MockQuery(self.model, self.items[n:])

    def limit(self, n):
        return MockQuery(self.model, self.items[:n])

    def all(self):
        return self.items

    def first(self):
        return self.items[0] if self.items else None

    def count(self):
        return len(self.items)


# Serialization Helpers
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    from datetime import date
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    # Handle Enums
    if hasattr(obj, 'value'):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def load_db():
    import json
    import os
    from app.models.policy import Policy, PolicyStatus, ProductType, PaymentFrequency
    
    global MOCK_DATA_STORE
    
    # Simple file path
    db_file = "mock_db.json"
    
    if os.path.exists(db_file):
        try:
             with open(db_file, 'r') as f:
                 data = json.load(f)
                 
                 # clear store
                 MOCK_DATA_STORE.clear()
                 
                 # Reconstruct Policy objects
                 if "Policy" in data:
                     MOCK_DATA_STORE["Policy"] = []
                     for item_data in data["Policy"]:
                         # Convert date strings back to datetime
                         for field in ["created_at", "updated_at", "last_payment_date", "next_payment_date", "start_date", "end_date"]:
                             if item_data.get(field):
                                 try:
                                     item_data[field] = datetime.fromisoformat(item_data[field])
                                 except:
                                     pass
                         
                         # Handle UUIDs
                         try:
                             item_data["id"] = uuid.UUID(item_data["id"])
                             # user_id is now a string (Firebase UID), don't cast to UUID
                             # item_data["user_id"] = uuid.UUID(item_data["user_id"])
                         except:
                             pass
                             
                         # Handle Enums
                         if item_data.get("status"):
                             item_data["status"] = PolicyStatus(item_data["status"])
                         if item_data.get("coverage_type"):
                             item_data["coverage_type"] = ProductType(item_data["coverage_type"])
                         if item_data.get("payment_frequency"):
                             item_data["payment_frequency"] = PaymentFrequency(item_data["payment_frequency"])
                         
                         # Instantiate Policy
                         policy = Policy(**item_data)
                         MOCK_DATA_STORE["Policy"].append(policy)
        except Exception as e:
            print(f"Failed to load mock db: {e}")

def save_db():
    import json
    
    # Convert objects to dicts
    serializable_store = {}
    for key, items in MOCK_DATA_STORE.items():
        serializable_store[key] = []
        for item in items:
            item_dict = item.__dict__.copy()
            if "_sa_instance_state" in item_dict:
                 del item_dict["_sa_instance_state"]
            serializable_store[key].append(item_dict)
            
    with open("mock_db.json", 'w') as f:
        json.dump(serializable_store, f, default=json_serial, indent=2)

# Global flag to ensure load only happens once
DB_LOADED = False

class MockSession:
    def __init__(self):
        global DB_LOADED
        if not DB_LOADED:
            load_db()
            DB_LOADED = True
            
        self.new_items = []
        self.deleted_items = []

    def add(self, item):
        self.new_items.append(item)
        # Auto-generate ID if missing
        if not hasattr(item, 'id') or getattr(item, 'id') is None :
             item.id = uuid.uuid4() # Native UUID object
        
        now = datetime.now()
        if not hasattr(item, 'created_at') or getattr(item, 'created_at') is None:
            item.created_at = now
        if not hasattr(item, 'updated_at') or getattr(item, 'updated_at') is None:
            item.updated_at = now
            
        # Initialize other fields to None if missing to match SQL behavior?
        # Actually Pydantic models usually set defaults but this is SQLAlchemy model instantiation
        pass

    def commit(self):
        for item in self.new_items:
            model_name = type(item).__name__
            if model_name not in MOCK_DATA_STORE:
                MOCK_DATA_STORE[model_name] = []
            MOCK_DATA_STORE[model_name].append(item)
        
        self.new_items = []
        # Persist to disk
        save_db()

    def refresh(self, item):
        pass

    def rollback(self):
        self.new_items = []

    def close(self):
        pass

    def query(self, model):
        return MockQuery(model)
