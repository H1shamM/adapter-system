BASE_ADAPTER_SCHEMA = {
    "enabled": {
        "type": "boolean",
        "label": "Enabled",
        "required": True,
        "default": True,
    },
    "sync_interval": {
        "type": "number",
        "label": "Sync Interval (seconds)",
        "required": True,
        "min": 300,
        "default": 3600,
    },
    "priority": {
        "type": "select",
        "label": "Priority",
        "options": ["low", "medium", "high"],
        "default": "medium",
    },

    "asset_types": {
        "type": "multiselect",
        "label": "Assets Types",
        "required": True,
        "options": [],
        "default": [],
    },
    "base_url": {
        "type": "string",
        "label": "Base URL",
        "required": True,
    },
    "auth_type": {
        "type": "select",
        "label": "Authentication Type",
        "required": True,
        "options": ["none", "api_key", "bearer", "aws"],
        "default": "none",
    },
}

AUTH_SCHEMAS = {
    "none": {},
    "api_key": {
        "type": "string",
        "label": "API Key",
        "required": True,
    },
    "bearer": {
        "header": {
            "type": "string",
            "label": "Auth Header",
            "default": "Authorization",
        },
        "prefix": {
            "type": "string",
            "label": "Token Prefix",
            "default": "Bearer",
        },
        "token": {
            "type": "string",
            "label": "Token",
            "required": True,
        },
    },
    "aws": {
        "access_key": {
            "type": "string",
            "label": "Access Key",
            "required": True,
        },
        "secret_key": {
            "type": "string",
            "label": "Secret Key",
            "required": True,
        },
        "region": {
            "type": "string",
            "label": "AWS Region",
            "default": "us-east-1",
        },
    },
}

COINGECKO_SCHEMA = {
    **BASE_ADAPTER_SCHEMA,
    "asset_types": {
        **BASE_ADAPTER_SCHEMA["asset_types"],
        "options": ["crypto"],
        "default": ["crypto"],
    },
    "base_url": {
        **BASE_ADAPTER_SCHEMA["base_url"],
        "default": "https://api.coingecko.com",
    },
    "currency": {
        "type": "select",
        "label": "Currency",
        "required": True,
        "options": ["usd", "eur"],
        "default": "usd",
    },
}

JSONPLACEHOLDER_SCHEMA = {
    **BASE_ADAPTER_SCHEMA,
    "asset_types": {
        **BASE_ADAPTER_SCHEMA["asset_types"],
        "options": ["user"],
        "default": ["user"],
    },
    "base_url": {
        **BASE_ADAPTER_SCHEMA["base_url"],
        "default": "https://jsonplaceholder.typicode.com",
    },
}

RANDOMUSER_SCHEMA = {
    **BASE_ADAPTER_SCHEMA,
    "asset_types": {
        **BASE_ADAPTER_SCHEMA["asset_types"],
        "options": ["user"],
        "default": ["user"],
    },
    "base_url": {
        **BASE_ADAPTER_SCHEMA["base_url"],
        "default": "https://randomuser.me/api",
    },
}

GITHUB_SCHEMA = {
    **BASE_ADAPTER_SCHEMA,
    "priority": {
        **BASE_ADAPTER_SCHEMA["priority"],
        "default": "high",
    },
    "asset_types": {
        **BASE_ADAPTER_SCHEMA["asset_types"],
        "options": ["repository", "user"],
        "default": ["repository"],
    },
    "base_url": {
        **BASE_ADAPTER_SCHEMA["base_url"],
        "default": "https://api.github.com",
    },
    "auth_type": {
        **BASE_ADAPTER_SCHEMA["auth_type"],
        "default": "none",
    },
    "repo": {
        "type": "string",
        "label": "Repository",
        "required": True,
        "example": "octocat"
    },
    "auth_config": {
        "type": "object",
        "label": "Authentication Configuration",
        "fields": {
            "header": {
                "type": "string",
                "label": "Auth Header",
                "default": "Authorization",
            },
            "prefix": {
                "type": "string",
                "label": "Token Prefix",
                "default": "Bearer",
            },
            "token": {
                "type": "string",
                "label": "Token",
                "required": True,
            },
        }
    },
}

AWS_SCHEMA = {
    **BASE_ADAPTER_SCHEMA,
    "priority": {
        **BASE_ADAPTER_SCHEMA["priority"],
        "default": "high",
    },
    "asset_types": {
        **BASE_ADAPTER_SCHEMA["asset_types"],
        "options": ["ec2", "s3", "iam"],
        "default": ["ec2", "s3"],
    },
    "auth_type": {
        **BASE_ADAPTER_SCHEMA["auth_type"],
        "default": "aws",
    },
    "services": {
        "type": "multiselect",
        "label": "AWS Services",
        "options": ["ec2", "s3", "iam"],
        "required": True,
        "default": ["ec2", "s3"],
    },
    "auth_config": {
        "type": "object",
        "label": "Authentication Configuration",
        "fields": {**AUTH_SCHEMAS['aws']}
    }
}

ADAPTER_SCHEMAS = {
    "coingecko": COINGECKO_SCHEMA,
    "jsonplaceholder": JSONPLACEHOLDER_SCHEMA,
    "randomuser": RANDOMUSER_SCHEMA,
    "github": GITHUB_SCHEMA,
    "aws": AWS_SCHEMA,
}
