import yaml

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def main():
    config = load_config(r'..//config//config.yaml')
    message = config.get('message','hello docker')

    print(f"message from config : { message }")


if __name__ == '__main__':
    main()
        
    