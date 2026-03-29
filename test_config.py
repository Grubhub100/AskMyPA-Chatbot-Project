import config

def test_config():
    try:
        print(f"LINKS['booking']: {config.LINKS['booking']}")
        print(f"SERVICES['treated_conditions'] length: {len(config.SERVICES['treated_conditions'])}")
        print(f"MESSAGES['pain']: {config.MESSAGES['pain']}")
        print(f"MESSAGES['error']: {config.MESSAGES['error']}")
        print(f"MESSAGES['demo_note']: {config.MESSAGES['demo_note']}")
        print(f"MESSAGES['disclaimer']: {config.MESSAGES['disclaimer']}")
        print("Verification SUCCESS: All config keys found.")
    except AttributeError as e:
        print(f"Verification FAILED: {e}")
    except KeyError as e:
        print(f"Verification FAILED: Key {e} not found in config dictionary.")

if __name__ == "__main__":
    test_config()
