import dash
from dash import dcc, html, Input, Output, State, callback
import pandas as pd
import plotly.express as px
import psycopg2
from dash.exceptions import PreventUpdate


# Database connection
def create_db_connection():
    return psycopg2.connect(
        host="localhost",
        user="postgres",
        password="sergine@008",
        database="expense_tracker",
        port="5432"
    )


def insert_transaction(amount, type, category, description, date):
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO transactions(amount, type, category, description, date) VALUES (%s, %s, %s, %s, %s)",
        (amount, type, category, description, date)
    )
    connection.commit()
    connection.close()


def fetch_transactions():
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    connection.close()
    return pd.DataFrame(rows, columns=["ID", "Amount", "Type", "Category", "Description", "Date"])


# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css"])

# # Updated App Layout
app.layout = html.Div([
    html.H1("Expense Tracker", className="text-5xl font-bold text-center py-6 text-white bg-gray-900 shadow-md"),

    html.Div([
        # Left Column (Form)
        html.Div([
            html.Label("Amount", className="block text-white font-medium mb-2"),
            dcc.Input(id="amount", type='number', className="w-full px-4 py-2 border bg-gray-700 text-white rounded-lg mb-3"),

            html.Label("Type (Expense or Income)", className="block text-white font-medium mb-2"),
            dcc.Dropdown(
                id='type',
                options=[
                    {'label': 'Expense', 'value': 'Expense'},
                    {'label': 'Income', 'value': 'Income'}
                ],
                value='Expense',
                className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 mb-4"
            ),

            html.Label("Category", className="block text-white font-medium mb-2"),
            dcc.Dropdown(
                id='category',
                options=[
                    {'label': 'Food', 'value': 'Food'},
                    {'label': 'Transportation', 'value': 'Transportation'},
                    {'label': 'Entertainment', 'value': 'Entertainment'},
                    {'label': 'Utilities', 'value': 'Utilities'}
                ],
                value='Food',
                className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 mb-4"
            ),

            html.Label("Description (Optional)", className="block text-white font-medium mb-2"),
            dcc.Input(id='description', type='text', className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg mb-4"),

            html.Label("Date (YYYY-MM-DD)", className="block text-white font-medium mb-2"),
            dcc.Input(id='date', type='text', className="w-full px-4 py-2 border bg-gray-700 text-white rounded-lg mb-4"),

            html.Button('Add Transaction', id='add-btn', n_clicks=0,
                        className="w-full bg-green-500 text-white px-4 py-2 rounded-lg shadow-md hover:bg-green-600")
        ], className="bg-gray-800 p-6 rounded-lg shadow-md flex-grow"),

        # Right Column (Summary + Category Chart)
        html.Div([
            html.H2("Summary", className="text-3xl font-bold text-white mb-4"),
            html.Div(id='summary', className="text-white text-lg mb-6"),

            html.H2("Category Breakdown", className="text-3xl font-bold text-white mb-4"),
            dcc.Graph(id='category-chart', className="rounded-lg shadow-md bg-gray-900 p-4")
        ], className="bg-gray-800 p-6 rounded-lg shadow-md flex-grow")
    ], className='flex space-x-6 p-6'),  # Flex container for equal sizing

    # Transaction Table (Spans Full Width)
    html.Div([
        html.H2("Transaction List", className="text-3xl font-bold text-white mb-4"),
        html.Div(id='transaction-table', className="overflow-x-auto bg-gray-800 rounded-lg shadow-md p-4")
    ], className="max-w-7xl mx-auto mb-6"),  # Adjusted max width for the full table

    # Export Button
    html.Div([
        html.Button("Export to CSV", id='export-btn', n_clicks=0,
                    className="bg-blue-500 text-white px-4 py-2 rounded-lg shadow-md hover:bg-blue-600"),
        dcc.Download(id='download-dataframe-csv')
    ], className="text-center")
], className="bg-gray-900 min-h-screen py-8")


# Callbacks
@callback(
    Output('transaction-table', 'children'),
    Output('summary', 'children'),
    Output('category-chart', 'figure'),
    Input('add-btn', 'n_clicks'),
    State('amount', 'value'),
    State('type', 'value'),
    State('category', 'value'),
    State('description', 'value'),
    State('date', 'value')
)
def update_table(n_clicks, amount, type, category, description, date):
    if n_clicks > 0:
        insert_transaction(amount, type, category, description, date)

    df = fetch_transactions()

    # Transaction Table
    table = html.Table([
        html.Thead(html.Tr([html.Th(col, className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider") for col in df.columns])),
        html.Tbody([
            html.Tr([html.Td(df.iloc[i][col], className="px-6 py-4 whitespace-nowrap text-sm text-gray-400") for col in df.columns],
                    className="bg-gray-800" if i % 2 == 0 else "bg-gray-700")
            for i in range(len(df))
        ])
    ], className="min-w-full divide-y divide-gray-600")

    # Summary
    total_expenses = df[df['Type'] == 'Expense']['Amount'].sum()
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    net_balance = total_income - total_expenses

    summary = html.Div([
        html.P(f"Total Expenses: ${total_expenses}", className="mb-2"),
        html.P(f"Total Income: ${total_income}", className="mb-2"),
        html.P(f"Net Balance: ${net_balance}", className="mb-2")
    ])

    # Category Chart
    category_data = df.groupby('Category')['Amount'].sum().reset_index()
    category_fig = px.bar(category_data, x='Category', y='Amount', title="Expenses by Category")

    return table, summary, category_fig


@callback(
    Output('download-dataframe-csv', 'data'),
    Input('export-btn', 'n_clicks')
)
def export_csv(n_clicks):
    if n_clicks == 0:
        raise PreventUpdate

    df = fetch_transactions()
    return dcc.send_data_frame(df.to_csv, "transactions.csv")


# Run Server
if __name__ == '__main__':
    app.run_server(debug=True)
