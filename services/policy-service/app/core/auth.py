from fastapi import Header
from typing import Optional

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        return {
            'user_id': '550e8400-e29b-41d4-a716-446655440000',
            'phone': '+225 07 07 07 07 07',
            'role': 'user'
        }
    role = "user"
    if authorization and "admin" in authorization.lower():
        role = "admin"

    return {
        'user_id': '550e8400-e29b-41d4-a716-446655440000',
        'phone': '+225 07 07 07 07 07',
        'role': role
    }
