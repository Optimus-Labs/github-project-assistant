#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Version
VERSION="0.1.0"

# Print banner
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}GitHub Project Assistant (GPA)${NC}"
echo -e "${BLUE}Installation Script v${VERSION}${NC}"
echo -e "${BLUE}================================${NC}"

# Detect OS and architecture
detect_os() {
  local os
  local arch

  case "$(uname -s)" in
  Darwin*) os="darwin" ;;
  Linux*) os="linux" ;;
  *) echo -e "${RED}Unsupported operating system${NC}" && exit 1 ;;
  esac

  case "$(uname -m)" in
  x86_64*) arch="amd64" ;;
  aarch64*) arch="arm64" ;;
  arm64*) arch="arm64" ;;
  *) echo -e "${RED}Unsupported architecture${NC}" && exit 1 ;;
  esac

  echo "$os-$arch"
}

# Detect package manager for Linux
detect_package_manager() {
  if [ -x "$(command -v apt-get)" ]; then
    echo "apt"
  elif [ -x "$(command -v yum)" ]; then
    echo "yum"
  elif [ -x "$(command -v pacman)" ]; then
    echo "pacman"
  else
    echo "unknown"
  fi
}

# Install dependencies
install_dependencies() {
  echo -e "${BLUE}Installing dependencies...${NC}"

  if [ "$(uname -s)" = "Darwin" ]; then
    if ! command -v brew >/dev/null 2>&1; then
      echo -e "${RED}Homebrew is required but not installed. Please install Homebrew first.${NC}"
      exit 1
    fi
    brew install python3
  else
    local pkg_manager=$(detect_package_manager)
    case $pkg_manager in
    apt)
      sudo apt-get update
      sudo apt-get install -y python3 python3-pip
      ;;
    yum)
      sudo yum install -y python3 python3-pip
      ;;
    pacman)
      sudo pacman -Sy python python-pip
      ;;
    *)
      echo -e "${RED}Unsupported package manager. Please install Python 3 manually.${NC}"
      exit 1
      ;;
    esac
  fi
}

# Download and install GPA
install_gpa() {
  local os_arch=$(detect_os)
  local tmp_dir=$(mktemp -d)
  local download_url="https://github.com/Optimus-Labs/github-project-assistant/releases/download/v${VERSION}/gpa-${VERSION}-${os_arch}.tar.gz"

  echo -e "${BLUE}Downloading GPA...${NC}"
  curl -L -o "${tmp_dir}/gpa.tar.gz" "${download_url}"

  echo -e "${BLUE}Installing GPA...${NC}"
  tar -xzf "${tmp_dir}/gpa.tar.gz" -C "${tmp_dir}"

  # Create installation directory
  sudo mkdir -p /opt/gpa
  sudo cp -r "${tmp_dir}/gpa"/* /opt/gpa/

  # Create symlink
  sudo ln -sf /opt/gpa/bin/gpa /usr/local/bin/gpa

  # Cleanup
  rm -rf "${tmp_dir}"
}

# Verify installation
verify_installation() {
  if command -v gpa >/dev/null 2>&1; then
    echo -e "${GREEN}GPA has been successfully installed!${NC}"
    echo -e "${BLUE}You can now use the 'gpa' command.${NC}"
  else
    echo -e "${RED}Installation failed. Please try again or install manually.${NC}"
    exit 1
  fi
}

# Main installation process
main() {
  install_dependencies
  install_gpa
  verify_installation

  echo -e "\n${BLUE}Next steps:${NC}"
  echo "1. Set up your environment variables:"
  echo "   export GROQ_API_KEY='your-groq-api-key'"
  echo "   export GITHUB_TOKEN='your-github-token'"
  echo "2. Run 'gpa --help' to see available commands"
}

# Run main installation
main
