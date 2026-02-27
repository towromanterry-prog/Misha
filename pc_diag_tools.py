# pc_diag_tools.py
import subprocess
import platform
import os
import psutil
from logger import get_logger

log = get_logger(__name__)

# --- ПОИСК ВПН КЛИЕНТОВ ---

def find_vpn_clients():
    """Ищет установленные и запущенные ВПН клиенты на ПК"""
    vpn_found = []
    
    if platform.system() == "Windows":
        vpn_list = find_vpn_windows()
    elif platform.system() == "Darwin":  # macOS
        vpn_list = find_vpn_macos()
    else:  # Linux
        vpn_list = find_vpn_linux()
    
    return vpn_list

def find_vpn_windows():
    """Ищет ВПН клиентов на Windows"""
    vpn_found = []
    vpn_processes = {
        'OpenVPN': ['openvpn.exe', 'openvpn-gui.exe'],
        'Cisco VPN': ['cvpnd.exe', 'ipsecdialer.exe'],
        'NordVPN': ['NordVPN.exe'],
        'ExpressVPN': ['expressvpn.exe'],
        'Surfshark': ['Surfshark.exe'],
        'ProtonVPN': ['ProtonVPN.exe'],
        'Mullvad': ['mullvad.exe'],
        'TorGuard': ['torguard.exe'],
        'PureVPN': ['PureVPN.exe'],
        'CyberGhost': ['CyberGhost.exe'],
        'PIA': ['pia.exe'],
        'Hotspot Shield': ['hssvc.exe'],
        'ZenMate': ['zenmate.exe'],
        'Windscribe': ['windscribe.exe'],
        'IPVanish': ['ipvanish.exe'],
        'VyprVPN': ['vyprvpn.exe'],
        'Private Internet Access': ['pia_manager.exe'],
        'SaferVPN': ['SaferVPN.exe'],
        'KeepSolid VPN': ['keepsolidvpn.exe'],
    }
    
    try:
        # Получаем список всех процессов
        running_processes = {p.name().lower() for p in psutil.process_iter(['name'])}
        
        # Проверяем наличие ВПН клиентов
        for vpn_name, process_names in vpn_processes.items():
            for proc_name in process_names:
                if proc_name.lower() in running_processes:
                    vpn_found.append(f"✅ {vpn_name} (процесс: {proc_name})")
                    log.info(f"Найден ВПН клиент: {vpn_name}")
                    break
        
        # Если ничего не найдено
        if not vpn_found:
            vpn_found.append("❌ ВПН клиентов не найдено")
            log.info("ВПН клиентов не найдено")
    
    except Exception as e:
        log.error(f"Ошибка поиска ВПН: {e}")
        vpn_found.append(f"⚠️ Ошибка при поиске: {str(e)[:50]}")
    
    return vpn_found

def find_vpn_macos():
    """Ищет ВПН клиентов на macOS"""
    vpn_found = []
    vpn_apps = [
        'OpenVPN',
        'Cisco VPN',
        'NordVPN',
        'ExpressVPN',
        'Surfshark',
        'ProtonVPN',
        'Mullvad',
        'TorGuard',
    ]
    
    try:
        for vpn in vpn_apps:
            app_path = f"/Applications/{vpn}.app"
            if os.path.exists(app_path):
                vpn_found.append(f"✅ {vpn} (установлен)")
                log.info(f"Найден ВПН клиент на macOS: {vpn}")
        
        # Проверка запущенных процессов
        running_processes = {p.name().lower() for p in psutil.process_iter(['name'])}
        vpn_process_names = ['openvpn', 'nordvpn', 'expressvpn', 'protonvpn', 'mullvad']
        
        for proc in vpn_process_names:
            if proc in running_processes:
                vpn_found.append(f"✅ {proc.upper()} (запущен)")
        
        if not vpn_found:
            vpn_found.append("❌ ВПН клиентов не найдено")
    
    except Exception as e:
        log.error(f"Ошибка поиска ВПН на macOS: {e}")
        vpn_found.append(f"⚠️ Ошибка: {str(e)[:50]}")
    
    return vpn_found

def find_vpn_linux():
    """Ищет ВПН клиентов на Linux"""
    vpn_found = []
    vpn_commands = {
        'OpenVPN': 'which openvpn',
        'WireGuard': 'which wg',
        'strongSwan': 'which ipsec',
        'L2TP': 'which xl2tpd',
    }
    
    try:
        for vpn_name, cmd in vpn_commands.items():
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                vpn_found.append(f"✅ {vpn_name} (установлен)")
                log.info(f"Найден ВПН клиент на Linux: {vpn_name}")
        
        if not vpn_found:
            vpn_found.append("❌ ВПН клиентов не найдено")
    
    except Exception as e:
        log.error(f"Ошибка поиска ВПН на Linux: {e}")
        vpn_found.append(f"⚠️ Ошибка: {str(e)[:50]}")
    
    return vpn_found

# --- ПОИСК АНТИВИРУСА ---

def find_antivirus():
    """Ищет установленные антивирусные программы"""
    antivirus_found = []
    
    if platform.system() == "Windows":
        antivirus_list = find_antivirus_windows()
    elif platform.system() == "Darwin":  # macOS
        antivirus_list = find_antivirus_macos()
    else:  # Linux
        antivirus_list = find_antivirus_linux()
    
    return antivirus_list

def find_antivirus_windows():
    """Ищет антивирусные программы на Windows"""
    antivirus_found = []
    antivirus_list = {
        'Windows Defender': ['MsMpEng.exe', 'SecurityHealthService.exe'],
        'Norton AntiVirus': ['NortonAntiVirus.exe', 'ccsvchst.exe'],
        'McAfee': ['mcods.exe', 'mcagent.exe'],
        'Kaspersky': ['avp.exe', 'kavfs.exe'],
        'ESET': ['ekrn.exe', 'egui.exe'],
        'Bitdefender': ['bdagent.exe', 'vsserv.exe'],
        'Avast': ['AvastUI.exe', 'AvastSvc.exe'],
        'AVG': ['avgui.exe', 'avgidsagent.exe'],
        'Trend Micro': ['tmwfp.exe', 'TiMiniService.exe'],
        'F-Secure': ['fshoster32.exe', 'fssm32.exe'],
        'Panda': ['PavService.exe', 'PandaAV.exe'],
        'Sophos': ['SophosUI.exe', 'SavService.exe'],
        'Symantec': ['symantec.exe', 'ccsvchst.exe'],
        'G-Data': ['AVKService.exe', 'AVKWatchService.exe'],
        'Comodo': ['cmdagent.exe', 'cavwp.exe'],
        'BullGuard': ['BullGuardAntivirus.exe', 'BgCtlPanel.exe'],
        'K7': ['K7TSecurity.exe', 'K7TotalSecurity.exe'],
        'Quick Heal': ['qlactive.exe', 'qh.exe'],
    }
    
    try:
        running_processes = {p.name().lower() for p in psutil.process_iter(['name'])}
        
        for av_name, process_names in antivirus_list.items():
            for proc_name in process_names:
                if proc_name.lower() in running_processes:
                    antivirus_found.append(f"✅ {av_name} (процесс: {proc_name})")
                    log.info(f"Найден антивирус: {av_name}")
                    break
        
        if not antivirus_found:
            antivirus_found.append("⚠️ Антивирусные программы не найдены")
            log.warning("Антивирусные программы не найдены")
    
    except Exception as e:
        log.error(f"Ошибка поиска антивируса: {e}")
        antivirus_found.append(f"⚠️ Ошибка при поиске: {str(e)[:50]}")
    
    return antivirus_found

def find_antivirus_macos():
    """Ищет антивирусные программы на macOS"""
    antivirus_found = []
    antivirus_apps = [
        'Sophos Central',
        'Norton',
        'McAfee',
        'Kaspersky',
        'ESET',
        'Bitdefender',
        'F-Secure',
        'Trend Micro',
        'Avast',
        'AVG',
    ]
    
    try:
        for av in antivirus_apps:
            app_path = f"/Applications/{av}.app"
            if os.path.exists(app_path):
                antivirus_found.append(f"✅ {av} (установлен)")
                log.info(f"Найден антивирус на macOS: {av}")
        
        if not antivirus_found:
            antivirus_found.append("⚠️ Антивирусные программы не найдены")
    
    except Exception as e:
        log.error(f"Ошибка поиска антивируса на macOS: {e}")
        antivirus_found.append(f"⚠️ Ошибка: {str(e)[:50]}")
    
    return antivirus_found

def find_antivirus_linux():
    """Ищет антивирусные программы на Linux"""
    antivirus_found = []
    antivirus_packages = {
        'ClamAV': 'which clamscan',
        'AVG': 'which avgd',
        'Sophos': 'which savdctl',
        'F-Secure': 'which fsscan',
        'ESET': 'which esets_scan',
        'Kaspersky': 'which kav',
    }
    
    try:
        for av_name, cmd in antivirus_packages.items():
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                antivirus_found.append(f"✅ {av_name} (установлен)")
                log.info(f"Найден антивирус на Linux: {av_name}")
        
        if not antivirus_found:
            antivirus_found.append("⚠️ Антивирусные программы не найдены")
    
    except Exception as e:
        log.error(f"Ошибка поиска антивируса на Linux: {e}")
        antivirus_found.append(f"⚠️ Ошибка: {str(e)[:50]}")
    
    return antivirus_found
