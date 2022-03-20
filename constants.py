DECIMAL_PATTERN = '^[\-\+]?[0-9]+([\.\,][0-9]+)?$'
LIMIT = 10
TABLE = ('''<!DOCTYPE html>
    <html>
    <style>
    table, td, th {{
      border: 1px solid black;
      border-collapse: collapse;
      font-size: 120%;
    }}
    td {{
        font-family: sans-serif;
    }}
    th {{
      background-color: #CBFAFB;
      width: 100px;
    }}
    h2 {{
      text-decoration-line: underline;
      font-size: 250%;
      style="font-family:courier;"
    }}
    
    </style>
    <body>
    <h2 align="center">Your list of transactions</h2>
    
    <table style="width:100%">
      <tr>
        <th><strong>Date</strong></th>
        <th><strong>Time</strong></th>
        <th><strong>Value</strong></th>
      </tr>
      <tr>
        <td>{}</td>
      </tr>>
    </table>
    
    
    </body>
    </html>
    ''')
