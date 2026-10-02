"""
WSGI giriş noktası — IIS HttpPlatformHandler / Waitress.
"""
from app import app as application

# Geriye uyumluluk: bazı hostlar `app` bekler
app = application
