import time
import jwt
from datetime import datetime, timedelta
from typing import Optional

from core.config import settings


class JitsiService:
    """
    Jitsi Meet JWT token generation and room management service.
    Enables secure, authenticated video consultations with HIPAA compliance.
    """
    
    def __init__(self):
        self.domain = settings.JITSI_DOMAIN
        self.app_id = settings.JITSI_APP_ID
        self.app_secret = settings.JITSI_APP_SECRET
        self.algorithm = settings.JITSI_JWT_ALGORITHM
        
        if not self.app_secret:
            raise ValueError("JITSI_APP_SECRET must be set in environment variables")
    
    def generate_token(
        self,
        room_name: str,
        user_name: str,
        user_email: str,
        user_id: str,
        is_moderator: bool = False,
        expires_in_hours: int = 24,
        user_avatar: Optional[str] = None,
    ) -> str:
        """
        Generate JWT token for Jitsi Meet authentication.
        
        Args:
            room_name: Unique room identifier
            user_name: Display name for user
            user_email: User email address
            user_id: Unique user identifier
            is_moderator: Grant moderator privileges (providers = True)
            expires_in_hours: Token expiration time
            user_avatar: Optional avatar URL
        
        Returns:
            JWT token string
        """
        now = int(time.time())
        exp = now + (expires_in_hours * 3600)
        
        payload = {
            # Standard JWT claims
            "iss": self.app_id,
            "aud": self.app_id,
            "sub": self.domain,
            "iat": now,
            "exp": exp,
            "nbf": now - 10,  # Not before (10 seconds grace period)
            
            # Jitsi-specific claims
            "room": room_name,
            "context": {
                "user": {
                    "id": user_id,
                    "name": user_name,
                    "email": user_email,
                    "avatar": user_avatar or "",
                },
                "group": "carefusion"
            },
            
            # Moderator privileges
            "moderator": is_moderator,
            
            # Features
            "features": {
                "livestreaming": False,  # Disable livestreaming
                "recording": is_moderator,  # Only moderators can record
                "transcription": False,
                "outbound-call": False,
                "sip-outbound-call": False,
            }
        }
        
        token = jwt.encode(payload, self.app_secret, algorithm=self.algorithm)
        return token
    
    def generate_room_name(self, appointment_id: str, org_id: int) -> str:
        """
        Generate secure, unique room name for appointment.
        
        Args:
            appointment_id: Appointment identifier
            org_id: Organization ID
        
        Returns:
            Unique room name
        """
        # Use appointment ID + timestamp for uniqueness
        timestamp = int(time.time())
        room_name = f"carefusion-{org_id}-{appointment_id}-{timestamp}"
        return room_name
    
    def create_meeting_config(
        self,
        room_name: str,
        token: str,
        user_name: str,
        is_moderator: bool = False,
    ) -> dict:
        """
        Create Jitsi Meet configuration object for frontend.
        
        Args:
            room_name: Room identifier
            token: JWT authentication token
            user_name: Display name
            is_moderator: Moderator status
        
        Returns:
            Configuration dictionary for Jitsi API
        """
        config = {
            "domain": self.domain,
            "roomName": room_name,
            "jwt": token,
            "configOverwrite": {
                "startWithAudioMuted": False,
                "startWithVideoMuted": False,
                "enableWelcomePage": False,
                "prejoinPageEnabled": True,
                "requireDisplayName": True,
                "enableInsecureRoomNameWarning": True,
                "disableThirdPartyRequests": True,
                "enableNoAudioDetection": True,
                "enableNoisyMicDetection": True,
                "resolution": 720,
                "constraints": {
                    "video": {
                        "height": {"ideal": 720, "max": 1080, "min": 360}
                    }
                },
                # Recording (moderators only)
                "fileRecordingsEnabled": is_moderator,
                "liveStreamingEnabled": False,
                # Lobby/waiting room
                "enableLobbyChat": True,
            },
            "interfaceConfigOverwrite": {
                "SHOW_JITSI_WATERMARK": False,
                "SHOW_WATERMARK_FOR_GUESTS": False,
                "SHOW_BRAND_WATERMARK": False,
                "BRAND_WATERMARK_LINK": "",
                "DEFAULT_BACKGROUND": "#1a1a1a",
                "DEFAULT_LOGO_URL": "",
                "PROVIDER_NAME": "FusionEMS CareFusion",
                "HIDE_INVITE_MORE_HEADER": True,
                "MOBILE_APP_PROMO": False,
                "TOOLBAR_BUTTONS": [
                    "microphone",
                    "camera",
                    "closedcaptions",
                    "desktop",
                    "fullscreen",
                    "fodeviceselection",
                    "hangup",
                    "chat",
                    "recording" if is_moderator else None,
                    "settings",
                    "raisehand",
                    "videoquality",
                    "tileview",
                    "download",
                    "help",
                    "mute-everyone",
                    "security",
                ],
                "SETTINGS_SECTIONS": [
                    "devices",
                    "language",
                    "moderator" if is_moderator else None,
                    "profile",
                ],
            },
            "userInfo": {
                "displayName": user_name,
            },
        }
        
        # Remove None values from toolbar
        config["interfaceConfigOverwrite"]["TOOLBAR_BUTTONS"] = [
            btn for btn in config["interfaceConfigOverwrite"]["TOOLBAR_BUTTONS"] if btn
        ]
        config["interfaceConfigOverwrite"]["SETTINGS_SECTIONS"] = [
            section for section in config["interfaceConfigOverwrite"]["SETTINGS_SECTIONS"] if section
        ]
        
        return config
    
    def validate_token(self, token: str) -> dict:
        """
        Validate JWT token and extract claims.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload
        
        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.app_secret,
                algorithms=[self.algorithm],
                audience=self.app_id,
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")


# Singleton instance
_jitsi_service = None


def get_jitsi_service() -> JitsiService:
    """Get or create JitsiService singleton instance."""
    global _jitsi_service
    if _jitsi_service is None:
        _jitsi_service = JitsiService()
    return _jitsi_service
