#!/bin/bash

conda create -n NERF_TURRET python=3.7
conda activate NERF_TURRET
pip install -r requirements.txt

platform=$(uname)

if [ "$platform" == "Darwin" ]; then
  echo "You are running macOS."

  if command -v cmake >/dev/null 2>&1; then
    echo "CMake is already installed."
  else
    echo "CMake is not installed."
    sudo port install cmake
  fi

elif [ "$platform" == "Linux" ]; then

  # Check for Ubuntu specifically
  if [ -f /etc/lsb-release ] || [ -f /etc/issue ]; then
    distro=$(grep -Ei 'Debian|Ubuntu|Linux Mint' /etc/issue)

    if [[ ! -z "$distro" ]]; then
      echo "You are running Ubuntu or a Ubuntu-based distribution."
      if command -v cmake >/dev/null 2>&1; then
        echo "CMake is already installed."
      else
        echo "CMake is not installed."
        sudo apt update && sudo apt upgrade
        sudo apt install cmake
        cmake --version
      fi


    else
      echo "You are running Linux, but not Ubuntu or a Ubuntu-based distribution. Please install the following packages manually"
    fi
  else
    echo "You are running Linux, but not Ubuntu or a Ubuntu-based distribution. Please install the following packages manually"
  fi
else
  echo "Unknown platform."
fi
