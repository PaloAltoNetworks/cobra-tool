import webbrowser
import json

from pathlib import Path


# with open("./core/aws-scenario-1-output.json", "r") as file:
#     data = json.load(file)

# ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"]
# WEB_SERVER_PUBLIC_IP = data["Web Server Public IP"]
# ATTACKER_SERVER_INSTANCE_ID = data["Attacker Server Instance ID"]
# WEB_SERVER_INSTANCE_ID = data["Web Server Instance ID"]

def gen_report(attacker_vm_id, attacker_vm_ip, infected_vm_id, infected_vm_ip ):
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CNBAS Attack Path Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                color: #333;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            header {
                text-align: center;
                margin-bottom: 40px;
            }
            header img {
                max-width: 200px;
                margin-bottom: 20px;
            }
            h1, h2, h3 {
                color: #333;
                text-align: center;
            }
            img {
                max-width: 100%;
                height: auto;
                margin-bottom: 20px;
                border-radius: 5px;
                box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            table, th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            .controls {
                list-style-type: none;
                padding-left: 0;
            }
            .controls li {
                margin-bottom: 10px;
            }
            .vertical-table {
                display: flex;
                flex-direction: row;
            }
            .vertical-table td {
                padding: 5px 10px;
            }
            .vertical-table .resource-type {
                font-weight: bold;
            }

        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <img src="core/scenarios/cnbas-logo.png" alt="CNBAS Logo">
                <h1 style="color: #4285F4;">CNBAS Attack Path Report</h1>
            </header>
            <section class="attack-description">
                <h2 style="color: #EA4335;">Description of Attack Path Scenario</h2>
                <p>Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning.</p>
            </section>
            <section>
                <h2 style="color: #34A853;">Attack Path Graph</h2>
                <img src="core/scenarios/cnbas-as-1.png" alt="Attack Path Graph">
            </section>
            <section>
                <h2 style="color: #FBBC05;">Resource Meta Data</h2>
                <table class="vertical-table">
                    <tbody>
                        <tr>
                            <td class="resource-type">Attacker VM ID:</td>
                            <td>'''+attacker_vm_id+'''</td>
                        </tr>
                        <tr>
                            <td class="resource-type">Attacker VM IP :</td>
                            <td>'''+attacker_vm_ip+'''</td>
                        </tr>
                        <tr>
                            <td class="resource-type">Infected VM ID:</td>
                            <td>'''+infected_vm_id+'''</td>
                        </tr>
                        <tr>
                            <td class="resource-type">Infected VM IP:</td>
                            <td>'''+infected_vm_ip+'''</td>
                        </tr>
                    </tbody>
                </table>
            </section>
            <section>
                <h2 style="color: #4285F4;">List of Controls to Evaluate Post-Attack</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Controls</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Check if controls can identify Vulnerabilities in EC2 instances</td>
                        </tr>
                        <tr>
                            <td>Check if controls can identify IAM high-privileged run-instance and pass-role permissions</td>
                        </tr>
                        <tr>
                            <td>Check if controls can identify anomaly activity through their threat detection</td>
                        </tr>
                        <tr>
                            <td>Check if controls can prevent the attack by blocking RCE payloads</td>
                        </tr>
                        <tr>
                            <td>Check if controls can able to identify metadata queries from audit logs</td>
                        </tr>
                        <tr>
                            <td>Check if controls logged the activity</td>
                        </tr>
                    </tbody>
                </table>
            </section>
        </div>
    </body>
    </html>
    '''

    with open("cnbas-as1-report.html", "w+") as file:
        file.write(html_template)
        

    print("HTML report generated successfully.")



#gen_report(ATTACKER_SERVER_INSTANCE_ID, ATTACKER_SERVER_PUBLIC_IP, WEB_SERVER_INSTANCE_ID, WEB_SERVER_PUBLIC_IP)
webbrowser.open_new_tab('file://'+ str(Path.cwd())+'/cnbas-as1-report.html')
    
