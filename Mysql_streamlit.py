import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as plt


# Function to connect to MySQL
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="23Nov1987@",   # replace with your MySQL password
        database="secure_check_db"   # replace with your database name
    )

def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
               cursor.execute(query)
               result = cursor.fetchall()
               columns = [desc[0] for desc in cursor.description]
               df = pd.DataFrame(result, columns=columns)
            return df
        except Exception as e:
            st.error(f"SQL Error: {e}")
            return pd.DataFrame()
        finally:
            connection.close()
    else:
        return pd.DataFrame()

# -----------------------------
# 2️⃣ Page Layout
# -----------------------------
st.set_page_config(page_title="Secure Check: Police check post digital ledger", layout="wide")

# 1. Title
st.title("🔒Secure Check 🚓 Traffic-Stop Analysis Dashboard")

# 2. Subtext
st.write("⚠️Real-time Monitoring and Law Enforcement Dashboard for Traffic Stops")

# 3. Subheader
st.subheader("📝Police Logs Overview")
query = "SELECT * FROM police_logs;"
data = fetch_data(query)
st.dataframe(data, use_container_width=True)


# -----------------------------
# 4️⃣ Dataset Load
# -----------------------------
#@st.cache_data
#def load_dataset():
    #query = "SELECT * FROM police_logs;"
    #return fetch_data(query)

#df = load_dataset()
#st.dataframe(df)

# -----------------------------
# 5️⃣ Key Metrics (In Statistics)
# -----------------------------
st.subheader("⚡Key Metrics")
# Average Stop Duration
query_avg_duration = """
SELECT  
    ROUND(AVG(
        CASE  
            WHEN stop_duration LIKE '%-%' THEN  
                (CAST(SUBSTRING_INDEX(stop_duration, '-', 1) AS DECIMAL(10,2)) +  
                 CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(stop_duration, '-', -1), ' ', 1) AS DECIMAL(10,2))) / 2
            WHEN stop_duration REGEXP '^[0-9]+$' THEN CAST(stop_duration AS DECIMAL(10,2))
            ELSE NULL
        END
    ), 2) AS average_stop_duration
FROM police_logs;
"""
avg_stop_duration = fetch_data(query_avg_duration)['average_stop_duration'][0]

# Average Driver Age
query_avg_age = "SELECT ROUND(AVG(driver_age),1) AS avg_driver_age FROM police_logs;"
avg_driver_age = fetch_data(query_avg_age)['avg_driver_age'][0]

# Arrest Rate
query_arrest_rate = """
SELECT ROUND(SUM(CASE WHEN is_arrested='True' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),2) AS arrest_rate
FROM police_logs;
"""
arrest_rate = fetch_data(query_arrest_rate)['arrest_rate'][0]

# Peak Stop Hour
query_peak_hour = """
SELECT HOUR(stop_time) AS peak_hour
FROM police_logs
GROUP BY peak_hour
ORDER BY COUNT(*) DESC
LIMIT 1;
"""
peak_hour = fetch_data(query_peak_hour)['peak_hour'][0]

# Top Violation
query_top_violation = """
SELECT violation
FROM police_logs
GROUP BY violation
ORDER BY COUNT(*) DESC
LIMIT 1;
"""
top_violation = fetch_data(query_top_violation)['violation'][0]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Avg Stop Duration", f"{avg_stop_duration} min")
col2.metric("Avg Driver Age", f"{avg_driver_age} yrs")
col3.metric("Arrest Rate", f"{arrest_rate}%")
col4.metric("Peak Stop Hour", f"{peak_hour}:00")
col5.metric("Top Violation", top_violation)

# -----------------------------
# 6️⃣ Visual Insights
# -----------------------------
st.subheader("📊Visual Insights")

# Stops by Violation
query_violations = """
SELECT violation, COUNT(*) AS total_stops
FROM police_logs
GROUP BY violation
ORDER BY total_stops DESC
LIMIT 10;
"""
df_violations = fetch_data(query_violations)
fig_violations = plt.bar(
    df_violations, 
    x='violation', 
    y='total_stops', 
    text='total_stops',
    labels={'total_stops':'Number of Stops','violation':'Violation'},
    color='total_stops', color_continuous_scale='blues'
)
st.plotly_chart(fig_violations, use_container_width=True)

# Driver Gender Distribution
query_gender = """
SELECT driver_gender, COUNT(*) AS total
FROM police_logs
GROUP BY driver_gender;
"""
df_gender = fetch_data(query_gender)
fig_gender = plt.pie(
    df_gender,
    names='driver_gender',
    values='total',
    title="Driver Gender Distribution",
    hole=0.4
)
st.plotly_chart(fig_gender, use_container_width=True)

# -----------------------------
# 7️⃣ Simple Insights (Fetch SQL 1-15)
# -----------------------------
st.subheader("🗂️Simple Insights")
# Example: Add as expandable sections for each query
# --- Define 15 Questions and Queries ---
questions = {
    "🚗 1. What are the top 10 vehicle numbers involved in drug-related stops?":
        """SELECT vehicle_number, COUNT(*) AS total_drug_stops
           FROM police_logs
           WHERE drug_related_stop = 'True'
           GROUP BY vehicle_number
           ORDER BY total_drug_stops
           LIMIT 10;""",

    "🚗 2. Which vehicles were most frequently searched?":
        """SELECT vehicle_number, COUNT(*) AS total_searches
           FROM police_logs
           WHERE search_conducted = 'True'
           GROUP BY vehicle_number
           ORDER BY total_searches DESC
           LIMIT 10;""",

    "🧍 3. Which driver age group had the highest arrest rate?":
        """SELECT CASE 
                    WHEN driver_age < 25 THEN 'Under 25'
                    WHEN driver_age BETWEEN 25 AND 40 THEN '25-40'
                    WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
                    ELSE '60+' END AS age_group,
                  AVG(is_arrested = 'True')*100 AS arrest_rate
           FROM police_logs
           GROUP BY age_group
           ORDER BY arrest_rate DESC;""",

    "🧍 4. What is the gender distribution of drivers stopped in each country?":
        """SELECT country_name, driver_gender, COUNT(*) AS total_stops
           FROM police_logs
           GROUP BY country_name, driver_gender
           ORDER BY country_name;""",

    "🧍 5. Which race and gender combination has the highest search rate?":
        """SELECT driver_gender, driver_race, 
                  AVG(search_conducted = 'True')*100 AS search_rate
           FROM police_logs
           GROUP BY driver_gender, driver_race
           ORDER BY search_rate DESC
           LIMIT 5;""",

    "🕒 6. What time of day sees the most traffic stops?":
        """SELECT HOUR(stop_time) AS hour_of_day, COUNT(*) AS total_stops
           FROM police_logs
           GROUP BY hour_of_day
           ORDER BY total_stops DESC;""",

    "🕒 7. What is the average stop duration for different violations?":
        """SELECT violation, AVG(stop_duration) AS avg_duration
           FROM police_logs
           GROUP BY violation
           ORDER BY avg_duration DESC;""",

    "🕒 8. Are stops during the night more likely to lead to arrests?":
        """SELECT CASE WHEN HOUR(stop_time) BETWEEN 20 AND 23 OR HOUR(stop_time) BETWEEN 0 AND 4 
                       THEN 'Night' ELSE 'Day' END AS period,
                  AVG(is_arrested = 'True')*100 AS arrest_rate
           FROM police_logs
           GROUP BY period;""",

    "⚖️ 9. Which violations are most associated with searches or arrests?":
        """SELECT violation,
                  AVG(search_conducted = 'True')*100 AS search_rate,
                  AVG(is_arrested = 'True')*100 AS arrest_rate
           FROM police_logs
           GROUP BY violation
           ORDER BY search_rate DESC, arrest_rate DESC
           LIMIT 10;""",

    "⚖️ 10. Which violations are most common among younger drivers (<25)?":
        """SELECT violation, COUNT(*) AS total_stops
           FROM police_logs
           WHERE driver_age < 25
           GROUP BY violation
           ORDER BY total_stops DESC;""",

    "⚖️ 11. Is there a violation that rarely results in search or arrest?":
        """SELECT violation,
           AVG(CASE WHEN search_conducted = 'True' THEN 1 ELSE 0 END)*100 AS search_rate,
           AVG(CASE WHEN is_arrested = 'True' THEN 1 ELSE 0 END)*100 AS arrest_rate
           FROM police_logs
           GROUP BY violation
           ORDER BY (AVG(CASE WHEN search_conducted = 'True' THEN 1 ELSE 0 END) 
           + AVG(CASE WHEN is_arrested = 'True' THEN 1 ELSE 0 END)) ASC LIMIT 5;""",

    "🌍 12. Which countries report the highest rate of drug-related stops?":
        """SELECT Country_name,
                 COUNT(*) AS total_stops,
                 SUM(CASE WHEN search_conducted = 'True' THEN 1 ELSE 0 END) AS total_searches
            FROM police_logs
            GROUP BY country_name
            ORDER BY total_searches DESC
            LIMIT 1;""",

    "🌍 13. What is the arrest rate by country and violation?":
        """SELECT country_name, violation,
                  AVG(is_arrested = 'True')*100 AS arrest_rate
           FROM police_logs
           GROUP BY country_name, violation
           ORDER BY arrest_rate DESC;""",

    "🌍 14. Which country has the most stops with search conducted?":
        """SELECT country_name, COUNT(*) AS total_searches
           FROM police_logs
           WHERE search_conducted = 'True'
           GROUP BY country_name
           ORDER BY total_searches DESC;""",
}

# --- Select Question ---
selected_question = st.selectbox("🔍 Select a question", list(questions.keys()))

# --- Run Query Button ---
def get_data():
    return pd.DataFrame()
if st.button("▶️ Run Query"):
    result = get_data()
    if not result.empty:
       st.write(result)
    else:
       st.warning("No results found for this query.")
# -----------------------------
# 8️⃣ Advanced Insights (Fetch SQL 1c-6c)
# -----------------------------
st.subheader("🧠Advanced Insights")
st.markdown("### 💡 Select an Advanced Question to Explore")

advanced_questions = {
    "1. Yearly Breakdown of Stops and Arrests by Country":
    """
    SELECT country_name, YEAR(stop_date) AS year,
           COUNT(*) AS total_stops,
           SUM(CASE WHEN is_arrested='True' THEN 1 ELSE 0 END) AS total_arrests
    FROM police_logs
    GROUP BY country_name, YEAR(stop_date)
    ORDER BY country_name, year;
    """,

    "2. Driver Violation Trends Based on Age and Gender":
    """
    SELECT 
         sub.age_group,
         sub.driver_gender,
         sub.violation,
          COUNT(*) AS total_violations
    FROM (
    SELECT 
        driver_gender,
        violation,
        CASE 
            WHEN driver_age < 25 THEN 'Under 25'
            WHEN driver_age BETWEEN 25 AND 40 THEN '25-40'
            WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
            ELSE '60+' 
        END AS age_group
    FROM police_logs
    WHERE driver_age IS NOT NULL AND driver_gender IS NOT NULL
        ) AS sub
    GROUP BY sub.age_group, sub.driver_gender, sub.violation
    ORDER BY sub.age_group, sub.driver_gender, total_violations DESC;
    """,

    "3. Time Period Analysis of Stops (Year, Month, Hour)":
    """
    SELECT YEAR(stop_date) AS year, 
           MONTH(stop_date) AS month,
           HOUR(stop_time) AS hour,
           COUNT(*) AS total_stops
    FROM police_logs
    GROUP BY year, month, hour
    ORDER BY year, month, hour;
    """,

    "4. Violations with High Search and Arrest Rates":
    """
    WITH violation_stats AS (
    SELECT
           violation,
           COUNT(*) AS total_stops,
           SUM(CASE WHEN search_conducted = 'True' THEN 1 ELSE 0 END) AS total_searches,
           SUM(CASE WHEN is_arrested = 'True' THEN 1 ELSE 0 END) AS total_arrests,
           ROUND(SUM(CASE WHEN search_conducted = 'True' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS search_rate_percent,
           ROUND(SUM(CASE WHEN is_arrested = 'True' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate_percent
        FROM police_logs
        GROUP BY violation
        )
    SELECT
           violation, total_stops, total_searches, total_arrests,
           search_rate_percent, arrest_rate_percent,
           RANK() OVER (ORDER BY search_rate_percent DESC) AS search_rank,
           RANK() OVER (ORDER BY arrest_rate_percent DESC) AS arrest_rank
        FROM violation_stats
        ORDER BY search_rate_percent DESC, arrest_rate_percent DESC
        LIMIT 10;""",

    "5. Driver Demographics by Country (Age, Gender)":
    """
    SELECT country_name,
           driver_gender,
           AVG(driver_age) AS avg_age,
           COUNT(*) AS total_stops
    FROM police_logs
    GROUP BY country_name, driver_gender
    ORDER BY country_name, total_stops DESC;
    """,

    "6. Top 5 Violations with Highest Arrest Rates":
    """
    SELECT violation,
           AVG(CASE WHEN is_arrested='True' THEN 1 ELSE 0 END)*100 AS arrest_rate,
           COUNT(*) AS total_stops
    FROM police_logs
    GROUP BY violation
    ORDER BY arrest_rate DESC
    LIMIT 5;
    """
}   
# Select Advanced Insight
selected_advanced_question = st.selectbox(
    "🔍 Select an Advanced Insight", 
    list(advanced_questions.keys())
)

# Initialize result
# --- Run Query Button ---
def get_data():
    return pd.DataFrame()
if st.button("▶️ Run Advanced Query"):
    adv_result = get_data()
    if not adv_result.empty:
        st.write(adv_result)
    else:
        st.warning("No results found for this query.")

       
st.markdown("---")
st.markdown("Built with 🛡️ for Law Enforcement By Securecheck")
st.subheader("🔍 Custom Natural Language Filter")
st.markdown("Fill in the details below to get a natural language prediction of the stop outcome based on existing data")
st.subheader("📝 Add New Police Log and Predict Outcome and Violation")

#input from all fields and excluding outputs
with st.form("Enter new log for prediction"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("Country Name")
    driver_gender = st.selectbox("Driver Gender", ["male","female"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
    search_conducted = st.selectbox("Was a Search Conducted?", ["0", "1"])
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.selectbox("Was Drug Related?", ["0", "1"])
    stop_duration = st.selectbox("Stop_Duration", data['Stop_duration'].dropna().unique())
    vehicle_number = st.text_input("Vehicle Number")
    timestamp = pd.Timestamp.now()
    
    submitted = st.form_submit_button("Predict stop outcome and violation")
    filtered_data = data.copy()
    if submitted:
        filtered_data = data.copy()  # start fresh
    if driver_gender != "Any":
        filtered_data = filtered_data[filtered_data['Driver_gender'] == driver_gender]
    if driver_age != "Any":
        filtered_data = filtered_data[filtered_data['Driver_age'] == driver_age]
    if search_conducted is not None:
        filtered_data = filtered_data[filtered_data['Search_conducted'] == search_conducted]
    if stop_duration != "Any":
        filtered_data = filtered_data[filtered_data['Stop_duration'] == stop_duration]
    if drugs_related_stop is not None:
        filtered_data = filtered_data[filtered_data['Drug_related_stop'] == drugs_related_stop]
  
    #st.dataframe(filtered_data)


    #Natural langauge summary
    #search_conducted = st.selectbox("Search Conducted?", ("Yes", "No"))
   # drug_related_stop = st.selectbox("Drugs_related_stop?", ("Yes", "No"))

    # Convert text input to integers
    #search_conducted = 1 if search_conducted == "Yes" else 0
    #drugs_related_stop = 1 if drugs_related_stop == "Yes" else 0

   # Create readable text
    search_text = "a search was conducted" if int(search_conducted) else "No search was conducted"
    drug_text = "was drug_related" if int(drugs_related_stop) else "was not drug_related"

    st.write(f"The stop {search_text} and {drug_text}.")

    #predict stop_outcome  
    if not filtered_data.empty:
         predicted_outcome = filtered_data["Stop_outcome"].mode()[0]
         predicted_violation = filtered_data['Violation'].mode()[0]
    else:
         predicted_outcome = "Warning"
         predicted_violation = "Speeding"  


    #search_text = "A search was conducted" if int(search_conducted) else "No search was conducted"
    #drug_text = "was drug_related" if int(drug_related_stops) else "was not drug_related"

    st.info(f"""
    **Prediction Summary**  
    - **Predicted Violation:** {predicted_violation}  
    - **Predicted Stop Outcome:** {predicted_outcome}

    A {driver_age}-year-old {driver_gender} driver in {country_name} was stopped at {stop_time.strftime('%I:%M %p')} on {stop_date}.
     a {search_text}, and the stop {drug_text}.
     Stop duration: **{stop_duration}**.
     Vehicle_number: **{vehicle_number}**.
    """)

