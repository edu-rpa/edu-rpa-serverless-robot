#!/bin/bash

bucket_name="edu-rpa-robot"
object_name="$ROBOT_FILE"

# Dependency map
declare -A dependency_map=(
    ["RPA.Cloud.Google"]="rpaframework-google"
    ["RPA.Cloud.AWS"]="rpaframework-aws"
    ["EduRPA"]="EduRPA"
    ["pytorch"]="pytorch torchvision cpuonly -c pytorch"
    ["PDF"]="rpaframework-pdf"
)

install_dependencies_from_robot_file() {
    # Read the contents of the Robot Framework file
    local robot_code=$1
    local dependencies=("robotframework" "rpaframework")
    
    imports=$(jq -r '.resource.imports[].name' <<< "$robot_code")
    
    for lib in $imports; do
        echo "Lib: $lib"
        if [[ -n ${dependency_map[$lib]} ]]; then
            dependencies+=(${dependency_map[$lib]})
        else
            parent_module=$(cut -d'.' -f1 <<< "$lib")

            if [[ -n ${dependency_map[$parent_module]} ]]; then
                dependencies+=(${dependency_map[$parent_module]})
            fi
        fi
    done
    
    dependencies=($(echo "${dependencies[@]}" | tr ' ' '\n' | awk '!seen[$0]++' | tr '\n' ' '))

    for dependency in "${dependencies[@]}"; do
        package_not_installed=($(check_package_installed "$dependency"))
        if [[ ${#package_not_installed[@]} -eq 0 ]]; then
            continue
        fi
        echo "Packages Not Installed: ${package_not_installed[*]}"

        install_command=("pip" "install" "-q" $dependency)
        echo "${install_command[@]}"
        "${install_command[@]}"

        if [[ $dependency == *"EduRPA"* ]]; then
            install_command=("conda" "install" "-y -q" ${dependency_map["pytorch"]})
            echo "${install_command[@]}"
            "${install_command[@]}"
        fi

        # Run the package install command
        echo "${install_command[@]}"
        "${install_command[@]}"
    done
}

# Download JSON file from S3
download_json_from_s3() {
    local bucket_name=$1
    local object_name=$2
    
    echo "====== Downloading robot code ======"
    aws s3 cp s3://$bucket_name/$object_name ./robot.json
}

# Check if package installed  
is_package_installed() {
    local package_name=$1
    [[ $(pip show "$package_name" 2>/dev/null) ]] && return 0 || return 1
}

check_package_installed() {
    local command=("$@")
    local package_not_installed=()

    for package in "${command[@]}"; do
        if [[ $package != -* && $package != http* ]]; then
            if [[ $package == *"=="* ]]; then
                package_name=$(cut -d'=' -f1 <<< "$package")
                installed_version=$(cut -d'=' -f2 <<< "$package")
            else
                package_name=$package
            fi
            if ! is_package_installed "$package_name"; then
                package_not_installed+=("$package_name")
            fi
        fi
    done

    echo "${package_not_installed[@]}"
}

wait_for_sync() {
    file="/opt/aws/amazon-cloudwatch-agent/logs/state/_var_log_robot.log"
    previous_checksum=""

    while true; do
        current_checksum=$(md5sum "$file" | awk '{print $1}')

        if [ "$current_checksum" != "$previous_checksum" ]; then
            previous_checksum="$current_checksum"
        else
            break
        fi
        sleep 10
    done
}

main() {
    download_json_from_s3 "$bucket_name" "$object_name"
    robot_code=$(<robot.json)
    create_robot_json_file() {
        echo "$robot_code" > ./robot.json
    }

    create_robot_json_file

    echo "====== Installing Dependencies ======"
    install_dependencies_from_robot_file "$robot_code"

    echo "====== Get Robot Credentials ======"
    get-credential

    echo "====== Running Robot ======"
    python3 -m robot robot.json

    echo "====== Turning off Robot ======"
    wait_for_sync
    sudo shutdown now
}

main
