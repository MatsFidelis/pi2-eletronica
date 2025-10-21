import time
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from signal import pause

# --- Configuração dos Pinos (Numeração BCM/GPIO) ---
LPWM_PIN = 12  # Conectado ao LPWM do BTS7960
RPWM_PIN = 13  # Conectado ao RPWM do BTS7960

# Pinos de Enable (Se estiverem conectados aos GPIOs. Se estiverem em 3.3V, remova estas linhas.)
L_EN_PIN = 17 # Conectado ao L_EN do BTS7960
R_EN_PIN = 27 # Conectado ao R_EN do BTS7960

# --- Inicialização dos Dispositivos ---
lpwm = PWMOutputDevice(LPWM_PIN)
rpwm = PWMOutputDevice(RPWM_PIN)

# Habilita o driver H. Define initial_value=True para HIGH/habilitado.
l_en = DigitalOutputDevice(L_EN_PIN, initial_value=True)
r_en = DigitalOutputDevice(R_EN_PIN, initial_value=True)

print(f"Teste do Motor DC (LPWM={LPWM_PIN}, RPWM={RPWM_PIN}) - Rampa de 10s")

# Função auxiliar para aceleração/desaceleração com tempo fixo
def ramp_speed_time(pwm_device, start_percent, end_percent, duration_s):
    """Muda a velocidade de forma suave durante um período de tempo (duration_s)."""

    # O passo é sempre de 1%
    direction = 1 if end_percent > start_percent else -1
    num_steps = abs(end_percent - start_percent)

    if num_steps == 0:
        return

    # Calcula o tempo de espera necessário para cada passo para atingir a duração total
    delay_s_per_step = duration_s / num_steps

    # Ajuste o loop para incluir o ponto final
    end_val = end_percent + direction

    for duty_percent in range(start_percent, end_val, direction):
        # Define o ciclo de trabalho entre 0.0 e 1.0
        duty_cycle = duty_percent / 100.0
        pwm_device.value = duty_cycle
        time.sleep(delay_s_per_step)

try:
    while True:
        print("\n--- INÍCIO DO CICLO ---")

        # 1. ACELERAÇÃO (30% a 100%) em 10 segundos
        rpwm.value = 0 # Garante que o pino reverso esteja desligado

        print("1. Acelerando de 30% para 100% (DURAÇÃO: 10 segundos)...")
        # 70 passos (100 - 30) * 0.1428s por passo = ~10s
        ramp_speed_time(lpwm, 30, 100, 10)

        # 2. ROTAÇÃO MÁXIMA (100%) por 10 segundos
        print("2. Mantendo a velocidade máxima (100%) por 10 segundos...")
        lpwm.value = 1.0 # Garante 100%
        time.sleep(10)

        # 3. DESACELERAÇÃO (100% a 0%) em 10 segundos
        print("3. Desacelerando de 100% para 0% (DURAÇÃO: 10 segundos)...")
        # 100 passos (100 - 0) * 0.1s por passo = 10s
        ramp_speed_time(lpwm, 100, 0, 10)

        print("--- CICLO CONCLUÍDO. Aguardando 3 segundos antes de repetir ---")
        time.sleep(3)

except KeyboardInterrupt:
    print("\nInterrompido pelo usuário.")

finally:
    # Garante que o motor pare completamente e desabilita os pinos na saída
    lpwm.off()
    rpwm.off()
    l_en.off()
    r_en.off()
    print("Motor parado e GPIOs limpos.")