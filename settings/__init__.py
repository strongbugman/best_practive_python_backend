from .base import *

if ENVIRONMENT == "test":
    from .test import *
elif ENVIRONMENT == "development":
    from .development import *
elif ENVIRONMENT == "integrated":
    from .integrated import *
elif ENVIRONMENT == "staging":
    from .staging import *
elif ENVIRONMENT == "production":
    from .production import *
