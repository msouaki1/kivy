from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
import telnetlib
import time
import re

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: '10dp'
    spacing: '10dp'

    GridLayout:
        cols: 1
        
        height: self.minimum_height
        spacing: '10dp'

        MDTextField:
            id: ip_input
            hint_text: 'Adresse IP du modem'
            
            height: '48dp'
            pos_hint: {'center_x': 0.5}
            input_type: 'number'

        MDLabel:
            id: info_label
            text: 'Informations Modem :'
            halign: 'center'
            theme_text_color: 'Secondary'
            font_style: 'H6'
            
            height: '48dp'
            pos_hint: {'center_x': 0.5}

    MDRaisedButton:
        text: 'Obtenir Infos Modem'
        on_press: app.fetch_modem_info()
        size_hint: None, None
        size: '150dp', '48dp'
        pos_hint: {'center_x': 0.5}




'''


class ModemInfoApp(MDApp):
    def build(self):
        return Builder.load_string(KV)

    def fetch_modem_info(self):
        ip_address = self.root.ids.ip_input.text
        login = 'root'
        password = 'ctAdmin'

        try:
            print(f"Tentative de connexion Telnet à {ip_address} avec login {login}...")
            tn = telnetlib.Telnet(ip_address)
            tn.read_until(b"Login: ")
            tn.write(login.encode('ascii') + b"\n")
            tn.read_until(b"Password: ")
            tn.write(password.encode('ascii') + b"\n")
            tn.read_until(b"> ")

            tn.write(b"adsl info --show\n")
            time.sleep(1)
            output = tn.read_until(b">").decode('ascii')

            tn.close()

            if not output.strip():
                print("La sortie de la commande adsl info --show est vide.")
                self.root.ids.info_label.text = "ADSL down"
                return

            parsed_info = self.parse_adsl_info(output)

            # Afficher les informations dans l'interface utilisateur
            if not parsed_info:
                self.root.ids.info_label.text = "ADSL down"
            else:
                info_text = f"Informations Modem :\n"
                for key, value in parsed_info.items():
                    info_text += f"{key}: {value}\n"

                self.root.ids.info_label.text = info_text

        except Exception as e:
            print(f"Erreur de connexion Telnet : {str(e)}")
            self.root.ids.info_label.text = f"Erreur de connexion Telnet : {str(e)}"

    def parse_adsl_info(self, output):
        parsed_info = {}
        mode_match = re.search(r"Mode:\s+(.+)", output)
        if mode_match:
            parsed_info['mode'] = mode_match.group(1)

        downstream_snr_match = re.search(r"SNR \(0.1 dB\):\s+(\d+)", output)
        if downstream_snr_match:
            parsed_info['downstream_snr'] = int(downstream_snr_match.group(1))

        upstream_snr_match = re.search(r"SNR \(0.1 dB\):\s+(\d+)", output)
        if upstream_snr_match:
            parsed_info['upstream_snr'] = int(upstream_snr_match.group(1))

        downstream_attn_match = re.search(r"Attn\(0.1 dB\):\s+(\d+)", output)
        if downstream_attn_match:
            parsed_info['downstream_attn'] = int(downstream_attn_match.group(1))

        upstream_attn_match = re.search(r"Attn\(0.1 dB\):\s+(\d+)", output)
        if upstream_attn_match:
            parsed_info['upstream_attn'] = int(upstream_attn_match.group(1))

        max_upstream_rate_match = re.search(r"Max:\s+Upstream rate = (\d+) Kbps, Downstream rate = (\d+) Kbps", output)
        if max_upstream_rate_match:
            parsed_info['max_upstream_rate'] = int(max_upstream_rate_match.group(1))
            parsed_info['max_downstream_rate'] = int(max_upstream_rate_match.group(2))

        bearer_upstream_rate_match = re.search(r"Bearer: 0, Upstream rate = (\d+) Kbps, Downstream rate = (\d+) Kbps", output)
        if bearer_upstream_rate_match:
            parsed_info['bearer_upstream_rate'] = int(bearer_upstream_rate_match.group(1))
            parsed_info['bearer_downstream_rate'] = int(bearer_upstream_rate_match.group(2))

        return parsed_info


if __name__ == '__main__':
    ModemInfoApp().run()
