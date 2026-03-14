import os
import tomllib
import tarfile
import datetime

def load_config():
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    
    return config

def create_tar_file(finalPath, files):
    with tarfile.open(finalPath, "w:gz") as tar:
        if len(files) == 1 and "*" in files[0]:
            dir_path = files[0][:-1] 
            files = [os.path.join(dir_path, f) for f in os.listdir(dir_path)]
        
        for path in files:
            if os.path.exists(path):
                tar.add(path, arcname=os.path.basename(path))
    return finalPath

def cleanup_backups(parent_backup_path, retention_count):
    if os.path.exists(parent_backup_path):
        dirs = [d for d in os.listdir(parent_backup_path) if os.path.isdir(os.path.join(parent_backup_path, d))]

        if len(dirs) > retention_count:
            dirs_sorted = sorted(dirs, reverse=True)
            dirs_to_delete = dirs_sorted[retention_count:]

            for d in dirs_to_delete:
                full_path = os.path.join(parent_backup_path, d)
                
                for root, dirs_sub, files_sub in os.walk(full_path, topdown=False):
                    for name in files_sub:
                        os.remove(os.path.join(root, name))
                    for name in dirs_sub:
                        os.rmdir(os.path.join(root, name))
               
                os.rmdir(full_path)

if __name__ == "__main__":
    config = load_config()

    if 'backups' not in config:
        print("'backups' section not found in config.toml")
        exit(1)

    backup_path = config['backups']['path'] + f'/{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
    retention_count = config['backups']['retention_count']

    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    
    for key, value in config.items():
        if key == 'backups':
            continue

        path = os.path.abspath(value["path"])
        
        files = []
        for file in value["files"]:
            files.append(os.path.join(path, file))

        docker = False

        if 'docker' in value and value['docker']:
           docker = True 

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tar_name = os.path.join(backup_path, f"{key}_backup_{timestamp}.tar.gz")
        
        if docker:
            os.system(f"docker compose -f {path}/docker-compose.yml down")
        
        tar_file = create_tar_file(tar_name, files)

        if docker:
            os.system(f"docker compose -f {path}/docker-compose.yml up -d")


        cleanup_backups(config['backups']['path'], retention_count)