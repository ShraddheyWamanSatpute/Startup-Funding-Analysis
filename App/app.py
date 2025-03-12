import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
import re



# Load Data
df = pd.read_excel("Data/Cleaned_Data.xlsx")
df_startup = pd.read_excel("Data/Cleaned_Data.xlsx", sheet_name="Sheet1")  
df_investor = pd.read_excel("Data/Cleaned_Data.xlsx", sheet_name="Sheet2")  
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')


# Navigation Bar
st.sidebar.title("Navigation")
analysis_option = st.sidebar.selectbox(
    "Select an analysis type:",
    ("General Analysis", "Startup Analysis", "Investor Analysis")
)

# Creating Columns: Year, Month, Year-Month
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['MonthYear'] = df['Date'].dt.strftime('%Y-%m')


# GENERAL ANALYSIS

def show_general_analysis(df):
    st.title("General Analysis")

    # Visual: Histogram with Line Chart
    # Month-over-Month chart -> Total Funding MoM & Count Of Deals
    st.subheader("Month over Month Funding & Deal Count")
    mom_df = df.groupby('MonthYear').agg({
        'Amount in INR': 'sum',
        'Startup': 'count'
    }).reset_index().rename(columns={'Startup': 'Deal Count'})

    mom_df['MonthYear_dt'] = pd.to_datetime(mom_df['MonthYear'], format='%Y-%m')
    mom_df.sort_values('MonthYear_dt', inplace=True)

    fig_mom = make_subplots(specs=[[{"secondary_y": True}]])
    fig_mom.add_trace(
        go.Bar(
            x=mom_df['MonthYear_dt'],
            y=mom_df['Deal Count'],
            name='Deal Count',
            marker_color='orange'
        ),
        secondary_y=False
    )
    fig_mom.add_trace(
        go.Scatter(
            x=mom_df['MonthYear_dt'],
            y=mom_df['Amount in INR'],
            name='Total Funding',
            line=dict(color='blue', width=2)
        ),
        secondary_y=True
    )

    fig_mom.update_layout(
        title_text="Month over Month (Total Funding vs Deal Count)",
        xaxis_title="Month",
        legend=dict(x=0.1, y=1.1, orientation='h'),
        hovermode='x'
    )
    fig_mom.update_yaxes(title_text="Deal Count", secondary_y=False)
    fig_mom.update_yaxes(title_text="Total Funding(cr)", secondary_y=True)

    st.plotly_chart(fig_mom, use_container_width=True)

    # Key Funding Metrics
    st.subheader("Key Funding Metrics")
    total_funding = df['Amount in INR'].sum()
    max_funding = df['Amount in INR'].max()
    avg_funding = df['Amount in INR'].mean()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Funding (Overall)", f"{round(total_funding,2):,}")
    with col2:
        st.metric("Max Funding in a Single Deal", f"{round(max_funding,2):,}")
    with col3:
        st.metric("Average Funding per Deal", f"{round(avg_funding,2):,}")

    # Vertical (Sector) Analysis Pie
    st.subheader("Vertical (Sector) Distribution")
    sector_choice = st.radio(
        "Show distribution by:",
        ("Deal Count", "Total Funding")
    )
    if sector_choice == "Deal Count":
        sector_df = df.groupby('Vertical')['Startup'].count().reset_index() \
                      .rename(columns={'Startup': 'Count'}) \
                      .sort_values('Count', ascending=False)
        title_text = "Vertical Distribution by Deal Count"
        values_col = 'Count'
    else:
        sector_df = df.groupby('Vertical')['Amount in INR'].sum().reset_index() \
                      .rename(columns={'Amount in INR': 'Total Funding'}) \
                      .sort_values('Total Funding', ascending=False)
        title_text = "Vertical Distribution by Total Funding"
        values_col = 'Total Funding'

    top_n = 10
    sector_df_top = sector_df.head(top_n)
    fig_sector = px.pie(
        sector_df_top,
        names='Vertical',
        values=values_col,
        title=title_text
    )
    st.plotly_chart(fig_sector, use_container_width=True)

    # Investment Round Distribution
    st.subheader("Investment Round Distribution")
    funding_type_df = df.groupby('Investment Round')['Startup'].count().reset_index() \
                        .rename(columns={'Startup': 'Count'}) \
                        .sort_values('Count', ascending=False).head(10)
    fig_funding_type = px.bar(
        funding_type_df,
        x='Investment Round',
        y='Count',
        color='Investment Round',
        title="Count of Deals by Investment Round"
    )
    st.plotly_chart(fig_funding_type, use_container_width=True)

    # City-wise Funding
    st.subheader("City-Wise Funding")
    city_df = df.groupby('City')['Amount in INR'].sum().reset_index() \
                .sort_values('Amount in INR', ascending=False)
    top_cities = city_df.head(10)
    fig_city = px.bar(
        top_cities,
        x='City',
        y='Amount in INR',
        color='City',
        title="Top 10 Cities by Total Funding"
    )
    st.plotly_chart(fig_city, use_container_width=True)

    # Top Funded Startups (Yearly or Overall)
    st.subheader("Top Funded Startups")
    years = sorted([x for x in df['Year'].unique() if pd.notnull(x)])
    selected_year = st.selectbox("Select Year (or 'Overall'):", ["Overall"] + list(map(str, years)))
    if selected_year == "Overall":
        top_startups_df = df.groupby('Startup')['Amount in INR'].sum() \
                            .reset_index().sort_values('Amount in INR', ascending=False)
    else:
        top_startups_df = df[df['Year'] == int(selected_year)] \
                          .groupby('Startup')['Amount in INR'].sum() \
                          .reset_index().sort_values('Amount in INR', ascending=False)

    st.write("Top 10 Funded Startups:")
    st.dataframe(top_startups_df.head(10))

    # Top Investors
    st.subheader("Top Investors")
    Investor_df = df.groupby('Investor')['Amount in INR'].sum().reset_index() \
                    .sort_values('Amount in INR', ascending=False)
    st.write("Top 10 Investors by Total Investment:")
    st.dataframe(Investor_df.head(10))

    # Funding Heatmap (Year vs Month)
    st.subheader("Funding Heatmap (Year vs. Month)")
    heatmap_df = df.groupby(['Year','Month'])['Amount in INR'].sum().reset_index()
    heatmap_pivot = heatmap_df.pivot(index='Year', columns='Month', values='Amount in INR').fillna(0)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(heatmap_pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax)
    ax.set_title("Heatmap of Funding by Year/Month")
    st.pyplot(fig)



# STARTUP ANALYSIS

def show_startup_analysis(df, selected_startup):
    st.title("Startup Analysis")

    # 2) Basic Info
    startup_data = df[df['Startup'] == selected_startup]
    industry = startup_data['Vertical'].mode()[0] if not startup_data['Vertical'].mode().empty else "Unknown"
    location = startup_data['City'].mode()[0] if not startup_data['City'].mode().empty else "Unknown"


    st.subheader("📌 Basic Info")
    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.write(f"#### 📝 Name: {selected_startup}")
        col2.write(f"#### 🏭 Industry: {industry}")
        col3.write(f"#### 📍 Location: {location}")


    total_funding = startup_data['Amount in INR'].sum()
    num_rounds = startup_data['Date'].nunique()
    earliest_date = startup_data['Date'].min()
    latest_date = startup_data['Date'].max()

    sorted_startup_data = startup_data['Date'].sort_values(ascending=True)
    earliest_funding_date = str(sorted_startup_data.iloc[0].date())
    latest_funding_date  = str(sorted_startup_data.iloc[-1].date())



    st.subheader("💰 Funding Overview")
    col1, col2 = st.columns(2)
    col1.metric("Total Funding", f"₹ {total_funding:,.2f} Cr")
    col2.metric("Number of Funding Rounds", num_rounds)
    col1.metric("Earliest Funding Date", earliest_funding_date)
    col2.metric("Latest Funding Date", latest_funding_date)
    




    funding_trend = startup_data.groupby('Date')['Amount in INR'].sum().reset_index()
    if not funding_trend.empty:
        st.subheader("📈 Funding Timeline")
        fig = px.line(funding_trend, x="Date", y="Amount in INR", markers=True,
                      title="Funding Over Time", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    



    st.subheader("📊 Funding Rounds")
    round_data = (
        startup_data[['Date', 'Investor', 'Amount in INR']]
        .sort_values('Date', ascending=True)
        .reset_index(drop=True)
    )

    if not round_data.empty:
        st.dataframe(round_data, use_container_width=True)
    else:
        st.info("No funding data available.")


    
    st.subheader("📍 Distinct Cities with Funding Rounds")

    distinct_cities = sorted(startup_data['City'].unique().tolist())

    cities_str = " | ".join([f"`{city}`" for city in distinct_cities])  
    st.markdown(f"#### {cities_str}")


    st.subheader("🔎 Similar Companies")
    similar_df = df[(df['Vertical'] == industry) & (df['Startup'] != selected_startup)]
    similar_companies = sorted(similar_df['Startup'].unique())[:5]
    for company in similar_companies:
        st.markdown(f"- **{company}**")  



# INVESTOR ANALYSIS
def show_investor_analysis(df_startup, df_investor, selected_investor):
    st.title("Investor Analysis")


    investor_funding_data = df_investor[df_investor['Investor'] == selected_investor]


    investor_details = df_startup[df_startup['Investor'].str.contains(selected_investor, case=False, na=False)]


    total_funding = investor_funding_data["Amount in INR"].sum()
    st.metric("Total Investment by Investor", f"₹ {total_funding:,.2f} Cr")

    st.subheader("📌 Recent Investments (Last 5)")
    recent_df = investor_details.sort_values("Date", ascending=False).head(5)
    st.dataframe(recent_df[['Date', 'Startup', 'Vertical', 'City', 'Investment Round', 'Amount in INR']], use_container_width=True)


    st.subheader("💰 Biggest Investments")
    biggest_df = investor_details.groupby("Startup")["Amount in INR"].sum().reset_index()
    biggest_df = biggest_df.sort_values("Amount in INR", ascending=False).head(5)

    fig_big = px.bar(biggest_df, x="Amount in INR", y="Startup",
                 orientation='h',  
                 color="Amount in INR", 
                 color_continuous_scale="Greens",  
                 title="Top 5 Biggest Investments",
                 labels={"Amount in INR": "Total Investment (INR)", "Startup": "Startup Name"},
                 template="plotly_dark")

    fig_big.update_yaxes(categoryorder="total ascending")
    fig_big.update_xaxes(tickangle=-45)  
    st.plotly_chart(fig_big, use_container_width=True)


    st.subheader("📊 Generally Invests In (Sector-wise)")
    sector_df = investor_details.groupby('Vertical')["Amount in INR"].sum().reset_index()
    sector_df = sector_df.sort_values("Amount in INR", ascending=False).head(10)
    if not sector_df.empty:
        fig_sector = px.pie(sector_df, names='Vertical', values='Amount in INR',
                            title="Sector (Vertical) Distribution by Total Investment",
                            template="plotly_dark")
        st.plotly_chart(fig_sector, use_container_width=True)


    st.subheader("📊 Investment Stage Distribution")
    stage_df = investor_details.groupby('Investment Round')["Amount in INR"].sum().reset_index()
    stage_df = stage_df.sort_values("Amount in INR", ascending=False).head(10)
    if not stage_df.empty:
        fig_stage = px.pie(stage_df, names='Investment Round', values='Amount in INR',
                           title="Stage (Round) Distribution by Total Investment",
                           template="plotly_dark")
        st.plotly_chart(fig_stage, use_container_width=True)


    st.subheader("📊 City-wise Investment Distribution")
    city_df = investor_details.groupby('City')["Amount in INR"].sum().reset_index()
    city_df = city_df.sort_values("Amount in INR", ascending=False).head(10)
    if not city_df.empty:
        fig_city = px.pie(city_df, names='City', values='Amount in INR',
                          title="City Distribution by Total Investment",
                          template="plotly_dark")
        st.plotly_chart(fig_city, use_container_width=True)


    st.subheader("📈 Year-over-Year (YoY) Investment")
    investor_details["Year"] = pd.to_datetime(investor_details["Date"]).dt.year
    yoy_df = investor_details.groupby("Year")["Amount in INR"].sum().reset_index()
    if not yoy_df.empty:
        fig_yoy = px.line(yoy_df, x="Year", y="Amount in INR", markers=True,
                          title=f"{selected_investor} – YoY Investment",
                          template="plotly_dark")
        st.plotly_chart(fig_yoy, use_container_width=True)


    st.subheader("🔍 Similar Investors")
    similar_investors = (
        df_investor[df_investor['Amount in INR'].between(total_funding * 0.8, total_funding * 1.2)]
        .sort_values("Amount in INR", ascending=False)["Investor"]
        .unique()
        .tolist()
    )

    similar_investors = [inv for inv in similar_investors if inv != selected_investor][:5]

    if similar_investors:
        st.write("**Investors with Similar Investment Amounts:**")
        for inv in similar_investors:
            st.markdown(f"- **{inv}**")
    else:
        st.write("No similar investors found.")



# Main Streamlit App Flow

# General Analysis Function call
if analysis_option == "General Analysis":
    show_general_analysis(df)

# Startup Analysis Function call 
elif analysis_option == "Startup Analysis":
    selected_startup = st.sidebar.selectbox('Select a Startup:', sorted(df['Startup'].unique().tolist()))
    btn1 = st.sidebar.button('Find StartUp Details')

    if btn1:
        show_startup_analysis(df, selected_startup)  


# Investor Analysis Function call 
elif analysis_option == "Investor Analysis":
    selected_investor = st.sidebar.selectbox('Select an Investor:', sorted(df_investor['Investor'].unique().tolist()))
    btn1 = st.sidebar.button('Find Investor Details')

    if btn1:
        show_investor_analysis(df_startup, df_investor, selected_investor)


