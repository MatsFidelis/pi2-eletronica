import time
import os
import sys # Para verificar o OS, se necessário, ou apenas para flush
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from signal import pause

# --- Configuração dos Pinos (Numeração BCM/GPIO) ---
LPWM_PIN = 12  # Conectado ao LPWM do BTS7960
RPWM_PIN = 13  # Conectado ao RPWM do BTS7960

# Pinos de Enable (Se estiverem conectados aos GPIOs. Se estiverem em 3.3V, remova estas linhas.)
L_EN_PIN = 17 # Conectado ao L_EN do BTS7960
R_EN_PIN = 27 # Conectado ao R_EN do BTS7960

# --- Inicialização dos Dispositivos ---
try:
    lpwm = PWMOutputDevice(LPWM_PIN)
    rpwm = PWMOutputDevice(RPWM_PIN)

    # Habilita o driver H. Define initial_value=True para HIGH/habilitado.
    l_en = DigitalOutputDevice(L_EN_PIN, initial_value=True)
    r_en = DigitalOutputDevice(R_EN_PIN, initial_value=True)
    
    # Garante que os enables estejam ativos
    l_en.on()
    r_en.on()

except Exception as e:
    print(f"ERRO: Não foi possível inicializar os dispositivos GPIO. Certifique-se de estar rodando em um Raspberry Pi com permissões sudo ou instale o mock-gpiozero para testes.")
    print(f"Detalhe do erro: {e}")
    # Define um modo 'mock' para que o resto do código possa ser testado
    class MockPWM:
        def __init__(self, pin):
            self.pin = pin
            self.value = 0.0
        def off(self):
            self.value = 0.0
        def on(self):
            self.value = 1.0
        def close(self):
            pass
    class MockDigital:
        def __init__(self, pin, initial_value):
            self.pin = pin
        def on(self):
            pass
        def off(self):
            pass
        def close(self):
            pass
            
    lpwm = MockPWM(LPWM_PIN)
    rpwm = MockPWM(RPWM_PIN)
    l_en = MockDigital(L_EN_PIN, True)
    r_en = MockDigital(R_EN_PIN, True)
    
    print("Continuando em modo de simulação (Mock GPIO). As operações reais no motor não ocorrerão.")


# ----------------------------------------------------------------------
# Funções de Auxílio
# ----------------------------------------------------------------------

def clear_terminal():
    """Limpa o terminal (compatível com Linux/Windows/macOS)."""
    os.system('cls' if os.name == 'nt' else 'clear')

def ramp_speed_time(pwm_device, start_percent, end_percent, duration_s):
    """Muda a velocidade de forma suave durante um período de tempo (duration_s)."""
    
    # Evita divisão por zero
    if duration_s <= 0:
        duration_s = 0.001
        
    # O passo é sempre de 1%
    direction = 1 if end_percent > start_percent else -1
    num_steps = abs(end_percent - start_percent)

    if num_steps == 0:
        pwm_device.value = end_percent / 100.0
        return

    # Calcula o tempo de espera necessário para cada passo para atingir a duração total
    delay_s_per_step = duration_s / num_steps
    
    # Ajuste o loop para incluir o ponto final (o range vai até end_percent + direction - 1)
    end_val = end_percent + direction 

    print(f"Iniciando rampa de {start_percent}% para {end_percent}% em {duration_s}s...")

    for duty_percent in range(start_percent, end_val, direction):
        # Define o ciclo de trabalho entre 0.0 e 1.0
        duty_cycle = duty_percent / 100.0
        
        # Garante que o duty cycle esteja entre 0.0 e 1.0 (ajuste por segurança)
        duty_cycle = max(0.0, min(1.0, duty_cycle))
        
        pwm_device.value = duty_cycle
        # Imprime o valor atual para feedback
        print(f"Duty Cycle: {duty_percent}% \r", end="", flush=True) 
        time.sleep(delay_s_per_step)
        
    print(f"Duty Cycle: {end_percent}% - Rampa concluída.                 ")


def stop_motor():
    """Para o motor (Opção 3)."""
    print("Parando o motor...")
    lpwm.off() # Desliga o PWM de avanço
    rpwm.off() # Desliga o PWM de ré
    # Poderíamos também desligar os Enables se quiséssemos (l_en.off(), r_en.off()), 
    # mas manter os PWMs em off geralmente é suficiente para o stop imediato.
    print("Motor parado.")
    
# ----------------------------------------------------------------------
# Opções do Menu
# ----------------------------------------------------------------------

def option_1_avancar_lento():
    """Avançar o motor: PWM de 30% a 100% em 3 segundos."""
    print("--- Opção 1: Avançar (30% a 100% em 3s) ---")
    
    # Garante que o sentido inverso esteja desligado
    rpwm.off() 
    
    # Avança
    ramp_speed_time(lpwm, 30, 100, 3.0)

def option_2_dar_re():
    """Dar ré: Inverter as polaridades (30% a 100% em 3 segundos)."""
    print("--- Opção 2: Dar Ré (30% a 100% em 3s, invertendo polaridade) ---")
    
    # Garante que o sentido de avanço esteja desligado
    lpwm.off() 
    
    # Inverte as polaridades (aciona o PWM reverso)
    ramp_speed_time(rpwm, 30, 100, 3.0)
    
def option_4_avancar_rapido():
    """Avançar o motor: PWM de 30% a 100% em 1 segundo."""
    print("--- Opção 4: Avançar Rápido (30% a 100% em 1s) ---")
    
    # Garante que o sentido inverso esteja desligado
    rpwm.off() 
    
    # Avança mais rápido
    ramp_speed_time(lpwm, 30, 100, 1.0)

# ----------------------------------------------------------------------
# Menu Principal
# ----------------------------------------------------------------------

def display_menu():
    """Exibe o menu de opções."""
    clear_terminal() # Tenta limpar o terminal para um menu mais limpo
    print("=======================================")
    print("          Controle do Motor DC         ")
    print("=======================================")
    print("1 - Avançar (PWM 30% a 100% em 3s)")
    print("2 - Dar Ré  (Inverter polaridade, 30% a 100% em 3s)")
    print("3 - Parar o Motor (Desligar PWM)")
    print("4 - Avançar Rápido (PWM 30% a 100% em 1s)")
    print("Q - Sair e Desligar GPIOs")
    print("=======================================")
    print("Selecione uma opção e pressione ENTER:")

def main_loop():
    """Loop principal do programa."""
    
    while True:
        display_menu()
        
        choice = input("Opção: ").strip().upper()
        
        print("\nProcessando...")

        if choice == '1':
            option_1_avancar_lento()
        elif choice == '2':
            option_2_dar_re()
        elif choice == '3':
            stop_motor()
        elif choice == '4':
            option_4_avancar_rapido()
        elif choice == 'Q':
            print("Saindo do programa.")
            break
        else:
            print("Opção inválida. Tente novamente.")
            time.sleep(1)
            continue # Volta para o topo do loop para exibir o menu

        # Após a execução da opção, solicita que o usuário pressione enter para voltar ao menu
        input("\nAção concluída. Pressione ENTER para retornar ao menu...")


# ----------------------------------------------------------------------
# Execução e Limpeza
# ----------------------------------------------------------------------

if __name__ == '__main__':
    try:
        main_loop()
        
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário (Ctrl+C).")
        
    finally:
        # Garante que o motor pare completamente e desabilita os pinos na saída
        print("\nRealizando limpeza dos GPIOs...")
        lpwm.off()
        rpwm.off()
        l_en.off() # Desliga o enable
        r_en.off() # Desliga o enable
        lpwm.close()
        rpwm.close()
        l_en.close()
        r_en.close()
        print("Motor parado e GPIOs limpos. Programa encerrado.")