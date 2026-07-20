import streamlit_authenticator as stauth
import yaml

hashed_password = stauth.Hasher.hash("your_test_password123")

config = {
    "credentials": {
        "usernames": {
            "faiza": {
                "email": "faiza@example.com",
                "name": "Faiza Tanveer",
                "password": hashed_password,
                "failed_login_attempts": 0,
                "logged_in": False
            }
        }
    },
    "cookie": {
        "name": "skill_atlas_auth",
        "key": "some_random_signature_key",
        "expiry_days": 7
    }
}

with open("config.yaml", "w") as f:
    yaml.dump(config, f)

print("config.yaml created.")