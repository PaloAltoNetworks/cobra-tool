import webbrowser
from pathlib import Path

def gen_report_2(API_GW_ID, LAMBDA_FUNC_ARN, API_GW_URL, LAMBDA_ROLE_NAME):
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>COBRA Attack Path Report</title>
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
                <img src="core/cnbas-logo.png" alt="COBRA Logo">
                <h1 style="color: #4285F4;">COBRA Attack Path Report</h1>
            </header>
            <section class="attack-description">
                <h2 style="color: #EA4335;">Attack Path Scenario Explained</h2>
                <p>The scenario simulates a real-world chained attack, beginning with the exploitation of a vulnerable application which is on Lambda, with an API GW. Subsequently, this initial breach facilitates a chain of events, including the credential dsicovery, exfiltration, escalation of credentials, and the anomalous provisioning of Backdoor IAM Role..</p>
            </section>

            <section>
                <h2 style="color: #34A853;">Attack Scenario Breakdown</h2>
                <p>1. Application is exploited through API GW, lambda backend</p>
                <p>2. Lambda Role credential is discovered and exfiltrated.</p>
                <p>3. Discovery of Privilege Escalation possibility with the exfiltrated credential.</p>
                <p>4. Attach Privileged Policy to the Role.</p>
                <p>5. Provision a Backdoor IAM Role to maintain persistence.</p>
                <p>6. Whitelist Attacker account id in the trust policy of the backdoor role.</p>
            </section>    

            <section>
                <h2 style="color: #34A853;">Attack Path Graph</h2>
                <img src="scenarios/scenario_2/report/cnbas-as-2.png" alt="Attack Path Graph">
            </section>
            <section>
                <h2 style="color: #FBBC05;">Resource Meta Data</h2>
                <table class="vertical-table">
                    <tbody>
                        <tr>
                            <td class="resource-type">API GW ID:</td>
                            <td>'''+API_GW_ID+'''</td>
                        </tr>
                        <tr>
                            <td class="resource-type">Lambda Function ARN :</td>
                            <td>'''+LAMBDA_FUNC_ARN+'''</td>
                        </tr>
                        <tr>
                            <td class="resource-type">API GW URL:</td>
                            <td>'''+API_GW_URL+'''</td>
                        </tr>
                        <tr>
                            <td class="resource-type">Lambda Role Name:</td>
                            <td>'''+LAMBDA_ROLE_NAME+'''</td>
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
                            <td>Check if API Gatway has Authentication & Autorization for APIs.</td>
                        </tr>
                        <tr>
                            <td>Check if API Gateway has WAF integrated which can stop L7 attacks.</td>
                        </tr>
                        <tr>
                            <td>Check if any Lambda has any defender layer which could prevent injection & credential exfil.</td>
                        </tr>
                        <tr>
                            <td>Check if Role Exfil and usage is being monitoried by eventbridge rules or cloudtrail monitoring.</td>
                        </tr>
                        <tr>
                            <td>Check if there are any SCPs which could prevent attaching privileged policies. </td>
                        </tr>
                        <tr>
                            <td>Check if new user/role/group creation is monitored.</td>
                        </tr>
                    </tbody>
                </table>
            </section>
        </div>
    </body>
    </html>
    '''

    with open("cobra-as2-report.html", "w+") as file:
        file.write(html_template)
        

    print("HTML report generated successfully.")
    webbrowser.open_new_tab('file://'+ str(Path.cwd())+'/cobra-as2-report.html')