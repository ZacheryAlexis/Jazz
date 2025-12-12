# Scripts

Utility scripts for Jazz RAG system setup and configuration.

## Environment Setup

### setup.sh (Linux/Mac)
```bash
./setup.sh
```
Initializes the Python environment, installs dependencies, and configures settings.

### setup.cmd (Windows)
```cmd
setup.cmd
```
Windows batch file for environment setup and configuration.

## Lab Configuration Scripts

These scripts configure lab environments and network settings:

### Lab 7 & 8 Setup
**lab7_lab8_complete.sh**
- Complete setup for both Lab 7 and Lab 8 environments
- Configures all necessary services and networking

**lab7_only.sh**
- Lab 7 specific configuration
- Sets up required components for Lab 7

**lab8_vlan_setup.sh**
- VLAN network configuration for Lab 8
- Configures network interfaces and routing

## Usage

```bash
# Initial setup
./setup.sh              # Linux/Mac
setup.cmd              # Windows

# Lab environment setup
bash lab7_lab8_complete.sh
bash lab7_only.sh
bash lab8_vlan_setup.sh
```

## Requirements

- Python 3.8+
- pip/conda for package management
- Bash (for .sh scripts)
- Appropriate permissions to install packages and configure network

## Troubleshooting

If setup fails:
1. Ensure Python is installed and in PATH
2. Check file permissions: `chmod +x *.sh`
3. Review the script output for specific errors
4. See main README for detailed requirements
