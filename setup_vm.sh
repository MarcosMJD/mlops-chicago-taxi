
echo "Starting user_data execution"

cd ~

# https://linuxcommand.org/lc3_man_pages/seth.html
# -a: all vars are marked at exportable
# -e Exit immediately if a command exits with a non-zero status.
# -x  Print commands and their arguments as they are executed.

set -ax

# echo -e enables interpretation of escape characters

if ! [ -d ./bin ];
then
    echo -e '\nCreating ~/bin directory\n'
    mkdir -p bin
fi

if ! [  -d ./bin/anaconda3 ]; then
    cd bin
    echo -e '\nInstalling anaconda3...\n'
    echo -e "Downloading anaconda3..."
    wget https://repo.anaconda.com/archive/Anaconda3-2022.05-Linux-x86_64.sh -O ./Anaconda3-2022.05-Linux-x86_64.sh
    echo -e "Running anaconda3 script..."
    # -b run install in batch mode (without manual intervention), it is expected the license terms are agreed upon
    # -p install prefix, defaults to $PREFIX, must not contain spaces.
    bash ./Anaconda3-2022.05-Linux-x86_64.sh -b -p ~/bin/anaconda3

    echo -e "Removing anaconda installation script..."
    rm ./Anaconda3-2022.05-Linux-x86_64.sh

    #activate conda
    eval "$(~/bin/anaconda3/bin/conda shell.bash hook)"

    echo -e "Running conda init..."
    conda init
    # Using -y flag to auto-approve
    echo -e "Running conda update..."
    conda update -y conda

    cd ~
else
    echo -e "anaconda already installed."
fi

echo "\nRunning sudo apt-get update...\n"
sudo apt-get update

echo -e "\nInstalling Docker...\n"
sudo apt-get -y install docker.io

echo -e "\nInstalling docker-compose...\n"
cd ~
cd bin
wget https://github.com/docker/compose/releases/download/v2.3.3/docker-compose-linux-x86_64 -O docker-compose
sudo chmod +x docker-compose

echo -e "\nInstalling Terraform...\n"
wget https://releases.hashicorp.com/terraform/1.3.0/terraform_1.3.0_linux_amd64.zip
sudo apt-get install unzip
unzip terraform_1.3.0_linux_amd64.zip
rm terraform_1.3.0_linux_amd64.zip

cd ~

echo -e "\nSetup .bashrc...\n"

echo -e '' >> ~/.bashrc
echo -e "export PATH=~/bin:$PATH" >> ~/.bashrc
echo -e '' >> ~/.bashrc
echo -e 'export PYTHONPATH=".:$PYTHONPATH"' >> ~/.bashrc

echo -e "\nSetting up Docker without sudo setup...\n"
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Specific stuff for the project

echo -e "\nCloning repo\n"
git clone https://github.com/MarcosMJD/mlops-chicago-taxi.git

cd mlops-chicago-taxi

echo -e "\nPreparing environment\n"
pip install --upgrade pip
pip install pipenv

cd sources
pipenv install --dev
