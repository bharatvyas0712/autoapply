from typing import Dict, Any, List

class SecurityAuthManager:
    """
    Validates JWT tokens, manages token refreshes, and checks Role-Based Access Controls (RBAC).
    """
    
    @staticmethod
    def generate_token_pair(user_id: int, role: str = "User") -> Dict[str, str]:
        return {
            "access_token": f"access_jwt_mock_{user_id}_{role}",
            "refresh_token": f"refresh_jwt_mock_{user_id}_{role}"
        }

    @staticmethod
    def verify_rbac(token: str, required_roles: List[str]) -> bool:
        # Expected formats: access_jwt_mock_{user_id}_{role}
        parts = token.split("_")
        if len(parts) >= 5:
            user_role = parts[4]
            if user_role in required_roles:
                return True
        return False
