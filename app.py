from shiny import App, render, ui, reactive
import polars as pl
from plotnine import *
import matplotlib.pyplot as plt
import io
import base64

# Load data
@reactive.calc
def load_data():
    leads_df = pl.read_csv('salesforce_leads.csv')
    platform_df = pl.read_csv('platform_performance.csv')
    quality_df = pl.read_csv('lead_quality_metrics.csv')
    
    # Convert date columns
    leads_df = leads_df.with_columns([
        pl.col('created_date').str.to_date('%Y-%m-%d'),
        pl.col('conversion_date').str.to_date('%Y-%m-%d')
    ])
    
    # Add company size categories
    leads_df = leads_df.with_columns(
        pl.when(pl.col('employees') < 50)
        .then(pl.lit('Small (< 50)'))
        .when(pl.col('employees') <= 250)
        .then(pl.lit('Medium (50-250)'))
        .when(pl.col('employees') <= 500)
        .then(pl.lit('Large (251-500)'))
        .otherwise(pl.lit('Enterprise (500+)'))
        .alias('company_size')
    )
    
    return leads_df, platform_df, quality_df

# Helper function to convert plotnine plot to base64 for Shiny
def plot_to_base64(plot, width=8, height=6, dpi=300):
    fig = plot.draw()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{img_str}"

# UI
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .sidebar {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .metric-card {
                background-color: white;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 15px;
                text-align: center;
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #2c3e50;
            }
            .metric-label {
                color: #7f8c8d;
                font-size: 0.9em;
            }
            .chart-container {
                text-align: center;
                margin-bottom: 20px;
            }
            .faq-answer {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-top: 15px;
                border-left: 4px solid #007bff;
            }
            .chat-container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .chat-response {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-top: 15px;
                border-left: 4px solid #28a745;
                max-height: 400px;
                overflow-y: auto;
            }
        """)
    ),
    
    ui.navset_tab(
        ui.nav_panel("Dashboard",
            ui.h1("Marketing Lead Quality Dashboard", style="text-align: center; color: #2c3e50; margin-bottom: 30px;"),
            ui.row(
            # Sidebar with filters
            ui.column(3,
                ui.div(
                    ui.h3("Filters", style="color: #34495e;"),
                    
                    ui.input_date_range(
                        "date_range",
                        "Date Range",
                        start="2024-01-01",
                        end="2024-06-30",
                        min="2024-01-01",
                        max="2024-12-31"
                    ),
                    
                    ui.input_checkbox_group(
                        "platforms",
                        "Platforms",
                        choices=["LinkedIn", "TikTok", "Events"],
                        selected=["LinkedIn", "TikTok", "Events"]
                    ),
                    
                    ui.input_checkbox_group(
                        "company_sizes",
                        "Company Size",
                        choices=["Small (< 50)", "Medium (50-250)", "Large (251-500)", "Enterprise (500+)"],
                        selected=["Small (< 50)", "Medium (50-250)", "Large (251-500)", "Enterprise (500+)"]
                    ),
                    
                    ui.input_selectize(
                        "industries",
                        "Industries",
                        choices=[],
                        selected=[],
                        multiple=True
                    ),
                    
                    ui.input_checkbox_group(
                        "lead_status",
                        "Lead Status",
                        choices=["Converted", "Qualified", "Opportunity", "Nurturing"],
                        selected=["Converted", "Qualified", "Opportunity", "Nurturing"]
                    ),
                    
                    ui.br(),
                    ui.download_button("download_data", "Download Filtered Data", class_="btn-primary"),
                    
                    class_="sidebar"
                )
            ),
            
            # Main content area
            ui.column(9,
                # KPI Cards
                ui.row(
                    ui.column(3, ui.output_ui("kpi_total_leads")),
                    ui.column(3, ui.output_ui("kpi_conversion_rate")),
                    ui.column(3, ui.output_ui("kpi_avg_deal_size")),
                    ui.column(3, ui.output_ui("kpi_total_revenue"))
                ),
                
                # Charts
                ui.row(
                    ui.column(6, ui.div(ui.output_ui("leads_trend_chart"), class_="chart-container")),
                    ui.column(6, ui.div(ui.output_ui("platform_performance_chart"), class_="chart-container"))
                ),
                
                ui.row(
                    ui.column(6, ui.div(ui.output_ui("conversion_funnel_chart"), class_="chart-container")),
                    ui.column(6, ui.div(ui.output_ui("lead_score_distribution"), class_="chart-container"))
                ),
                
                ui.row(
                    ui.column(12, ui.div(ui.output_ui("industry_performance_chart"), class_="chart-container"))
                ),
                
                ui.row(
                    ui.column(12, ui.div(ui.output_ui("revenue_analysis_chart"), class_="chart-container"))
                )
            )
        )
        ),
        ui.nav_panel("Lead Source FAQ",
            ui.div(
                ui.h1("Lead Source FAQ", style="text-align: center; color: #2c3e50; margin-bottom: 30px;"),
                ui.row(
                    ui.column(12,
                        ui.div(
                            ui.h3("Ask a Question About Your Lead Data", style="color: #34495e; margin-bottom: 20px;"),
                            ui.input_selectize(
                                "faq_question",
                                "Select a question:",
                                choices=[
                                    "Which platform generates the highest quality leads?",
                                    "What is the average conversion rate by industry?",
                                    "Which company size segment has the highest revenue potential?",
                                    "How do lead scores correlate with actual conversions?",
                                    "What are the seasonal trends in lead generation?",
                                    "Which industries have the fastest conversion times?",
                                    "What is the ROI comparison across different platforms?",
                                    "How does lead quality vary by geographic region?",
                                    "What are the characteristics of our best converting leads?",
                                    "Which time periods show the highest lead activity?"
                                ],
                                selected="Which platform generates the highest quality leads?"
                            ),
                            ui.output_ui("faq_answer"),
                            style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);"
                        )
                    )
                )
            )
        ),
        ui.nav_panel("QueryChat",
            ui.div(
                ui.h1("QueryChat - Ask Questions About Your Data", style="text-align: center; color: #2c3e50; margin-bottom: 30px;"),
                ui.row(
                    ui.column(12,
                        ui.div(
                            ui.h3("Ask any question about your lead data", style="color: #34495e; margin-bottom: 20px;"),
                            ui.p("Type your question in natural language. For example: 'How many leads did we get from LinkedIn last month?' or 'Which industry has the best conversion rate?'", 
                                style="color: #7f8c8d; margin-bottom: 20px;"),
                            ui.input_text_area(
                                "query_question",
                                "Your Question:",
                                placeholder="Ask anything about your lead data...",
                                height="100px"
                            ),
                            ui.input_action_button("submit_query", "Ask Question", class_="btn-primary"),
                            ui.output_ui("query_response"),
                            class_="chat-container"
                        )
                    )
                ),
                ui.row(
                    ui.column(12,
                        ui.div(
                            ui.h4("Example Questions:", style="color: #34495e; margin-bottom: 15px;"),
                            ui.tags.ul(
                                ui.tags.li("How many leads did we get from each platform this year?"),
                                ui.tags.li("What's the average deal size for Enterprise companies?"),
                                ui.tags.li("Which month had the highest conversion rate?"),
                                ui.tags.li("Show me all leads with scores above 90"),
                                ui.tags.li("What industries convert best for TikTok leads?"),
                                ui.tags.li("How does lead quality compare between platforms?")
                            ),
                            style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;"
                        )
                    )
                )
            )
        )
    )
)

# Server
def server(input, output, session):
    
    # Update industry choices based on data
    @reactive.effect
    def update_industry_choices():
        leads_df, _, _ = load_data()
        industries = sorted(leads_df['industry'].unique().to_list())
        ui.update_selectize("industries", choices=industries, selected=industries)
    
    # Filtered data
    @reactive.calc
    def filtered_data():
        leads_df, platform_df, quality_df = load_data()
        
        # Apply filters
        filtered_leads = leads_df
        
        # Date filter
        date_start, date_end = input.date_range()
        filtered_leads = filtered_leads.filter(
            (pl.col('created_date') >= pl.lit(date_start)) &
            (pl.col('created_date') <= pl.lit(date_end))
        )
        
        # Platform filter
        if input.platforms():
            filtered_leads = filtered_leads.filter(pl.col('platform').is_in(input.platforms()))
        
        # Company size filter
        if input.company_sizes():
            filtered_leads = filtered_leads.filter(pl.col('company_size').is_in(input.company_sizes()))
        
        # Industry filter
        if input.industries():
            filtered_leads = filtered_leads.filter(pl.col('industry').is_in(input.industries()))
        
        # Status filter
        if input.lead_status():
            filtered_leads = filtered_leads.filter(pl.col('status').is_in(input.lead_status()))
        
        return filtered_leads, platform_df, quality_df
    
    # KPI Cards
    @output
    @render.ui
    def kpi_total_leads():
        filtered_leads, _, _ = filtered_data()
        total_leads = filtered_leads.height
        return ui.div(
            ui.div(str(total_leads), class_="metric-value"),
            ui.div("Total Leads", class_="metric-label"),
            class_="metric-card"
        )
    
    @output
    @render.ui
    def kpi_conversion_rate():
        filtered_leads, _, _ = filtered_data()
        if filtered_leads.height > 0:
            conversion_rate = (filtered_leads.filter(pl.col('status') == 'Converted').height / filtered_leads.height) * 100
            return ui.div(
                ui.div(f"{conversion_rate:.1f}%", class_="metric-value"),
                ui.div("Conversion Rate", class_="metric-label"),
                class_="metric-card"
            )
        return ui.div(
            ui.div("0%", class_="metric-value"),
            ui.div("Conversion Rate", class_="metric-label"),
            class_="metric-card"
        )
    
    @output
    @render.ui
    def kpi_avg_deal_size():
        filtered_leads, _, _ = filtered_data()
        converted_leads = filtered_leads.filter(pl.col('status') == 'Converted')
        if converted_leads.height > 0:
            avg_deal = converted_leads['opportunity_value'].mean()
            return ui.div(
                ui.div(f"${avg_deal:,.0f}", class_="metric-value"),
                ui.div("Avg Deal Size", class_="metric-label"),
                class_="metric-card"
            )
        return ui.div(
            ui.div("$0", class_="metric-value"),
            ui.div("Avg Deal Size", class_="metric-label"),
            class_="metric-card"
        )
    
    @output
    @render.ui
    def kpi_total_revenue():
        filtered_leads, _, _ = filtered_data()
        converted_leads = filtered_leads.filter(pl.col('status') == 'Converted')
        total_revenue = converted_leads['opportunity_value'].sum()
        return ui.div(
            ui.div(f"${total_revenue:,.0f}", class_="metric-value"),
            ui.div("Total Revenue", class_="metric-label"),
            class_="metric-card"
        )
    
    # Charts
    @output
    @render.ui
    def leads_trend_chart():
        filtered_leads, _, _ = filtered_data()
        
        # Group by month and platform
        trend_data = (filtered_leads
                     .with_columns(pl.col('created_date').dt.strftime('%Y-%m').alias('month'))
                     .group_by(['month', 'platform'])
                     .agg(pl.len().alias('leads'))
                     .sort(['month', 'platform'])
                     .to_pandas())
        
        if len(trend_data) == 0:
            return ui.div("No data available")
        
        plot = (ggplot(trend_data, aes(x='month', y='leads', color='platform', group='platform')) +
                geom_line(size=1.2) +
                geom_point(size=2) +
                theme_minimal() +
                labs(title='Lead Generation Trends by Platform',
                     x='Month', y='Number of Leads', color='Platform') +
                theme(axis_text_x=element_text(rotation=45),
                      plot_title=element_text(size=14, weight='bold')))
        
        img_str = plot_to_base64(plot, width=8, height=5)
        return ui.img(src=img_str, style="max-width: 100%; height: auto;")
    
    @output
    @render.ui
    def platform_performance_chart():
        filtered_leads, _, _ = filtered_data()
        
        # Platform performance metrics
        platform_stats = (filtered_leads
                         .group_by('platform')
                         .agg([
                             pl.col('lead_score').mean().alias('avg_lead_score'),
                             (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate')
                         ])
                         .to_pandas())
        
        if len(platform_stats) == 0:
            return ui.div("No data available")
        
        plot = (ggplot(platform_stats, aes(x='platform')) +
                geom_col(aes(y='avg_lead_score'), fill='lightblue', alpha=0.7) +
                geom_point(aes(y='conversion_rate'), color='red', size=4) +
                geom_line(aes(y='conversion_rate', group=1), color='red', size=1) +
                theme_minimal() +
                labs(title='Platform Performance: Lead Score vs Conversion Rate',
                     x='Platform', y='Average Lead Score') +
                theme(plot_title=element_text(size=14, weight='bold')))
        
        img_str = plot_to_base64(plot, width=8, height=5)
        return ui.img(src=img_str, style="max-width: 100%; height: auto;")
    
    @output
    @render.ui
    def conversion_funnel_chart():
        filtered_leads, _, _ = filtered_data()
        
        # Conversion funnel by platform
        funnel_data = []
        for platform in filtered_leads['platform'].unique().to_list():
            platform_leads = filtered_leads.filter(pl.col('platform') == platform)
            total = platform_leads.height
            qualified = platform_leads.filter(pl.col('status').is_in(['Qualified', 'Opportunity', 'Converted'])).height
            converted = platform_leads.filter(pl.col('status') == 'Converted').height
            
            funnel_data.extend([
                {'platform': platform, 'stage': 'Total Leads', 'count': total},
                {'platform': platform, 'stage': 'Qualified', 'count': qualified},
                {'platform': platform, 'stage': 'Converted', 'count': converted}
            ])
        
        funnel_df = pl.DataFrame(funnel_data).to_pandas()
        
        if len(funnel_df) == 0:
            return ui.div("No data available")
        
        plot = (ggplot(funnel_df, aes(x='stage', y='count', fill='platform')) +
                geom_col(position='dodge') +
                theme_minimal() +
                labs(title='Conversion Funnel by Platform',
                     x='Stage', y='Number of Leads', fill='Platform') +
                theme(plot_title=element_text(size=14, weight='bold')))
        
        img_str = plot_to_base64(plot, width=8, height=5)
        return ui.img(src=img_str, style="max-width: 100%; height: auto;")
    
    @output
    @render.ui
    def lead_score_distribution():
        filtered_leads, _, _ = filtered_data()
        
        leads_pd = filtered_leads.to_pandas()
        
        if len(leads_pd) == 0:
            return ui.div("No data available")
        
        plot = (ggplot(leads_pd, aes(x='lead_score', fill='platform')) +
                geom_histogram(alpha=0.7, bins=20, position='identity') +
                theme_minimal() +
                labs(title='Lead Score Distribution by Platform',
                     x='Lead Score', y='Count', fill='Platform') +
                theme(plot_title=element_text(size=14, weight='bold')))
        
        img_str = plot_to_base64(plot, width=8, height=5)
        return ui.img(src=img_str, style="max-width: 100%; height: auto;")
    
    @output
    @render.ui
    def industry_performance_chart():
        filtered_leads, _, _ = filtered_data()
        
        # Industry performance
        industry_stats = (filtered_leads
                         .group_by('industry')
                         .agg([
                             pl.len().alias('lead_count'),
                             pl.col('lead_score').mean().alias('avg_lead_score'),
                             (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate')
                         ])
                         .filter(pl.col('lead_count') >= 2)
                         .to_pandas())
        
        if len(industry_stats) == 0:
            return ui.div("No data available")
        
        plot = (ggplot(industry_stats, aes(x='avg_lead_score', y='conversion_rate', size='lead_count')) +
                geom_point(alpha=0.7) +
                theme_minimal() +
                labs(title='Industry Performance: Lead Score vs Conversion Rate',
                     x='Average Lead Score', y='Conversion Rate (%)', size='Lead Count') +
                theme(plot_title=element_text(size=14, weight='bold')))
        
        img_str = plot_to_base64(plot, width=10, height=5)
        return ui.img(src=img_str, style="max-width: 100%; height: auto;")
    
    @output
    @render.ui
    def revenue_analysis_chart():
        filtered_leads, _, _ = filtered_data()
        
        # Revenue by platform and company size
        revenue_data = (filtered_leads
                       .filter(pl.col('status') == 'Converted')
                       .group_by(['platform', 'company_size'])
                       .agg(pl.col('opportunity_value').sum().alias('revenue'))
                       .to_pandas())
        
        if len(revenue_data) == 0:
            return ui.div("No data available")
        
        plot = (ggplot(revenue_data, aes(x='company_size', y='revenue', fill='platform')) +
                geom_col(position='dodge') +
                theme_minimal() +
                labs(title='Revenue by Company Size and Platform',
                     x='Company Size', y='Revenue ($)', fill='Platform') +
                theme(axis_text_x=element_text(rotation=45),
                      plot_title=element_text(size=14, weight='bold')) +
                scale_y_continuous(labels=lambda l: [f'${x/1000:.0f}K' for x in l]))
        
        img_str = plot_to_base64(plot, width=10, height=5)
        return ui.img(src=img_str, style="max-width: 100%; height: auto;")
    
    # Download handler
    @session.download(filename="filtered_leads.csv")
    def download_data():
        filtered_leads, _, _ = filtered_data()
        return filtered_leads.write_csv()
    
    # FAQ Analysis Functions
    def analyze_platform_quality():
        leads_df, _, _ = load_data()
        platform_stats = (leads_df
                         .group_by('platform')
                         .agg([
                             pl.col('lead_score').mean().alias('avg_lead_score'),
                             (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate'),
                             pl.len().alias('total_leads'),
                             pl.col('opportunity_value').filter(pl.col('status') == 'Converted').mean().alias('avg_deal_size')
                         ])
                         .sort('avg_lead_score', descending=True))
        
        top_platform = platform_stats.row(0)
        return f"Based on your data, **{top_platform[0]}** generates the highest quality leads with an average lead score of {top_platform[1]:.1f} and a conversion rate of {top_platform[2]:.1f}%. This platform has generated {top_platform[3]} total leads with an average deal size of ${top_platform[4]:,.0f} for converted leads."
    
    def analyze_conversion_by_industry():
        leads_df, _, _ = load_data()
        industry_stats = (leads_df
                         .group_by('industry')
                         .agg([
                             (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate'),
                             pl.len().alias('lead_count')
                         ])
                         .filter(pl.col('lead_count') >= 3)
                         .sort('conversion_rate', descending=True))
        
        top_industries = industry_stats.head(3)
        result = "**Top converting industries:**\n\n"
        for i, row in enumerate(top_industries.iter_rows()):
            result += f"{i+1}. **{row[0]}**: {row[1]:.1f}% conversion rate ({row[2]} leads)\n"
        
        avg_conversion = leads_df.filter(pl.col('status') == 'Converted').height / leads_df.height * 100
        result += f"\nOverall average conversion rate: {avg_conversion:.1f}%"
        return result
    
    def analyze_company_size_revenue():
        leads_df, _, _ = load_data()
        converted_leads = leads_df.filter(pl.col('status') == 'Converted')
        size_stats = (converted_leads
                     .group_by('company_size')
                     .agg([
                         pl.col('opportunity_value').sum().alias('total_revenue'),
                         pl.col('opportunity_value').mean().alias('avg_deal_size'),
                         pl.len().alias('converted_count')
                     ])
                     .sort('total_revenue', descending=True))
        
        top_segment = size_stats.row(0)
        result = f"**{top_segment[0]}** companies have the highest revenue potential with ${top_segment[1]:,.0f} in total revenue from {top_segment[3]} converted leads.\n\n"
        result += f"Average deal size for this segment: ${top_segment[2]:,.0f}\n\n"
        result += "**Revenue breakdown by company size:**\n"
        for row in size_stats.iter_rows():
            result += f"• {row[0]}: ${row[1]:,.0f} total (${row[2]:,.0f} avg deal)\n"
        return result
    
    def analyze_lead_score_correlation():
        leads_df, _, _ = load_data()
        converted = leads_df.filter(pl.col('status') == 'Converted')
        non_converted = leads_df.filter(pl.col('status') != 'Converted')
        
        converted_avg_score = converted['lead_score'].mean()
        non_converted_avg_score = non_converted['lead_score'].mean()
        
        high_score_conversion = leads_df.filter(pl.col('lead_score') >= 80).filter(pl.col('status') == 'Converted').height
        high_score_total = leads_df.filter(pl.col('lead_score') >= 80).height
        high_score_rate = (high_score_conversion / high_score_total * 100) if high_score_total > 0 else 0
        
        result = f"**Lead Score Analysis:**\n\n"
        result += f"• Average lead score for converted leads: **{converted_avg_score:.1f}**\n"
        result += f"• Average lead score for non-converted leads: **{non_converted_avg_score:.1f}**\n"
        result += f"• Difference: **{converted_avg_score - non_converted_avg_score:.1f} points**\n\n"
        result += f"High-quality leads (score ≥80) convert at **{high_score_rate:.1f}%** ({high_score_conversion}/{high_score_total} leads)\n\n"
        result += "This shows that lead scores are a strong predictor of conversion success."
        return result
    
    def analyze_seasonal_trends():
        leads_df, _, _ = load_data()
        monthly_trends = (leads_df
                         .with_columns(pl.col('created_date').dt.strftime('%Y-%m').alias('month'))
                         .group_by('month')
                         .agg([
                             pl.len().alias('lead_count'),
                             (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate')
                         ])
                         .sort('month'))
        
        best_month = monthly_trends.sort('lead_count', descending=True).row(0)
        best_conversion_month = monthly_trends.sort('conversion_rate', descending=True).row(0)
        
        result = f"**Seasonal Lead Generation Trends:**\n\n"
        result += f"• **Highest volume month**: {best_month[0]} with {best_month[1]} leads\n"
        result += f"• **Best conversion month**: {best_conversion_month[0]} with {best_conversion_month[2]:.1f}% conversion rate\n\n"
        result += "**Monthly breakdown:**\n"
        for row in monthly_trends.iter_rows():
            result += f"• {row[0]}: {row[1]} leads ({row[2]:.1f}% conversion)\n"
        return result
    
    # FAQ Answer Handler
    @output
    @render.ui
    def faq_answer():
        question = input.faq_question()
        
        if not question:
            return ui.div("Please select a question to see the analysis.")
        
        try:
            if question == "Which platform generates the highest quality leads?":
                answer = analyze_platform_quality()
            elif question == "What is the average conversion rate by industry?":
                answer = analyze_conversion_by_industry()
            elif question == "Which company size segment has the highest revenue potential?":
                answer = analyze_company_size_revenue()
            elif question == "How do lead scores correlate with actual conversions?":
                answer = analyze_lead_score_correlation()
            elif question == "What are the seasonal trends in lead generation?":
                answer = analyze_seasonal_trends()
            else:
                answer = "This analysis is not yet implemented. Please select a different question."
            
            return ui.div(
                ui.h4(question, style="color: #2c3e50; margin-bottom: 15px;"),
                ui.markdown(answer),
                class_="faq-answer"
            )
        except Exception as e:
            return ui.div(
                ui.h4(question, style="color: #2c3e50; margin-bottom: 15px;"),
                ui.p(f"Unable to analyze this question due to data constraints: {str(e)}"),
                class_="faq-answer"
            )
    
    # QueryChat functionality
    def process_natural_language_query(question):
        """Process natural language questions and return data-driven answers"""
        leads_df, platform_df, quality_df = load_data()
        question_lower = question.lower()
        
        try:
            # Check for platform-specific industry queries first
            if ('industry' in question_lower or 'industries' in question_lower) and any(platform in question_lower for platform in ['tiktok', 'linkedin', 'events']):
                if 'convert' in question_lower or 'conversion' in question_lower:
                    # Check if question is asking about a specific platform
                    platform_filter = None
                    if 'tiktok' in question_lower:
                        platform_filter = 'TikTok'
                    elif 'linkedin' in question_lower:
                        platform_filter = 'LinkedIn'
                    elif 'events' in question_lower:
                        platform_filter = 'Events'
                    
                    # Filter by platform if specified
                    filtered_leads = leads_df.filter(pl.col('platform') == platform_filter) if platform_filter else leads_df
                    
                    if filtered_leads.height == 0:
                        return f"No leads found for {platform_filter}."
                    
                    # Handle null values in industry column
                    filtered_leads = filtered_leads.with_columns(
                        pl.col('industry').fill_null('Unknown Industry')
                    )
                    
                    industry_conversion = filtered_leads.group_by('industry').agg([
                        (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate'),
                        pl.len().alias('total_leads')
                    ]).filter(pl.col('total_leads') >= 1).sort('conversion_rate', descending=True)
                    
                    result = f"**Industry conversion rates for {platform_filter}:**\n\n"
                    
                    if industry_conversion.height == 0:
                        return f"No industries found for {platform_filter}."
                    
                    for row in industry_conversion.iter_rows():
                        result += f"• {row[0]}: {row[1]:.1f}% ({row[2]} leads)\n"
                    return result
            
            # Platform-related queries
            elif any(word in question_lower for word in ['platform', 'linkedin', 'tiktok', 'events']):
                if 'count' in question_lower or 'how many' in question_lower:
                    platform_counts = leads_df.group_by('platform').agg(pl.len().alias('count')).sort('count', descending=True)
                    result = "**Lead counts by platform:**\n\n"
                    for row in platform_counts.iter_rows():
                        result += f"• {row[0]}: {row[1]} leads\n"
                    return result
                
                elif 'quality' in question_lower or 'score' in question_lower:
                    platform_quality = leads_df.group_by('platform').agg([
                        pl.col('lead_score').mean().alias('avg_score'),
                        (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate')
                    ]).sort('avg_score', descending=True)
                    result = "**Platform quality comparison:**\n\n"
                    for row in platform_quality.iter_rows():
                        result += f"• {row[0]}: {row[1]:.1f} avg score, {row[2]:.1f}% conversion\n"
                    return result
            
            # Industry-related queries (general)
            elif 'industry' in question_lower or 'industries' in question_lower:
                if 'convert' in question_lower or 'conversion' in question_lower:
                    # Handle null values in industry column
                    leads_with_industry = leads_df.with_columns(
                        pl.col('industry').fill_null('Unknown Industry')
                    )
                    
                    industry_conversion = leads_with_industry.group_by('industry').agg([
                        (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate'),
                        pl.len().alias('total_leads')
                    ]).filter(pl.col('total_leads') >= 2).sort('conversion_rate', descending=True)
                    
                    result = "**Industry conversion rates:**\n\n"
                    
                    if industry_conversion.height == 0:
                        return "No industries with sufficient data found."
                    
                    for row in industry_conversion.iter_rows():
                        result += f"• {row[0]}: {row[1]:.1f}% ({row[2]} leads)\n"
                    return result
            
            # Company size queries
            elif any(word in question_lower for word in ['company size', 'enterprise', 'small', 'medium', 'large']):
                if 'deal size' in question_lower or 'revenue' in question_lower:
                    size_revenue = leads_df.filter(pl.col('status') == 'Converted').group_by('company_size').agg([
                        pl.col('opportunity_value').mean().alias('avg_deal'),
                        pl.col('opportunity_value').sum().alias('total_revenue'),
                        pl.len().alias('deals')
                    ]).sort('avg_deal', descending=True)
                    result = "**Revenue by company size:**\n\n"
                    for row in size_revenue.iter_rows():
                        result += f"• {row[0]}: ${row[1]:,.0f} avg deal, ${row[2]:,.0f} total ({row[3]} deals)\n"
                    return result
            
            # Monthly/seasonal queries
            elif any(word in question_lower for word in ['month', 'monthly', 'seasonal', 'trend']):
                monthly_data = leads_df.with_columns(
                    pl.col('created_date').dt.strftime('%Y-%m').alias('month')
                ).group_by('month').agg([
                    pl.len().alias('leads'),
                    (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate')
                ]).sort('month')
                
                if 'conversion' in question_lower:
                    best_month = monthly_data.sort('conversion_rate', descending=True).row(0)
                    result = f"**Monthly conversion rates:**\n\n"
                    result += f"Best month: {best_month[0]} with {best_month[2]:.1f}% conversion\n\n"
                    for row in monthly_data.iter_rows():
                        result += f"• {row[0]}: {row[2]:.1f}% conversion ({row[1]} leads)\n"
                else:
                    result = "**Monthly lead generation:**\n\n"
                    for row in monthly_data.iter_rows():
                        result += f"• {row[0]}: {row[1]} leads ({row[2]:.1f}% conversion)\n"
                return result
            
            # High score leads
            elif 'score above' in question_lower or 'high score' in question_lower:
                import re
                score_match = re.search(r'(\d+)', question_lower)
                threshold = int(score_match.group(1)) if score_match else 80
                
                high_score_leads = leads_df.filter(pl.col('lead_score') >= threshold)
                result = f"**Leads with scores ≥ {threshold}:**\n\n"
                result += f"Total: {high_score_leads.height} leads\n"
                
                platform_breakdown = high_score_leads.group_by('platform').agg(pl.len().alias('count')).sort('count', descending=True)
                result += "\n**By platform:**\n"
                for row in platform_breakdown.iter_rows():
                    result += f"• {row[0]}: {row[1]} leads\n"
                
                conversion_rate = (high_score_leads.filter(pl.col('status') == 'Converted').height / high_score_leads.height * 100) if high_score_leads.height > 0 else 0
                result += f"\n**Conversion rate**: {conversion_rate:.1f}%"
                return result
            
            # Lead quality comparison
            elif 'compare' in question_lower and 'quality' in question_lower:
                quality_comparison = leads_df.group_by('platform').agg([
                    pl.col('lead_score').mean().alias('avg_score'),
                    pl.col('lead_score').median().alias('median_score'),
                    (pl.col('status').eq('Converted').sum() / pl.len() * 100).alias('conversion_rate'),
                    pl.len().alias('total_leads')
                ]).sort('avg_score', descending=True)
                
                result = "**Lead Quality Comparison by Platform:**\n\n"
                for row in quality_comparison.iter_rows():
                    result += f"**{row[0]}:**\n"
                    result += f"  • Average Score: {row[1]:.1f}\n"
                    result += f"  • Median Score: {row[2]:.1f}\n"
                    result += f"  • Conversion Rate: {row[3]:.1f}%\n"
                    result += f"  • Total Leads: {row[4]}\n\n"
                return result
            
            # General data overview
            elif any(word in question_lower for word in ['overview', 'summary', 'total']):
                total_leads = leads_df.height
                converted_leads = leads_df.filter(pl.col('status') == 'Converted').height
                conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
                total_revenue = leads_df.filter(pl.col('status') == 'Converted')['opportunity_value'].sum()
                avg_deal_size = leads_df.filter(pl.col('status') == 'Converted')['opportunity_value'].mean()
                avg_lead_score = leads_df['lead_score'].mean()
                
                result = "**Data Overview:**\n\n"
                result += f"• **Total Leads**: {total_leads}\n"
                result += f"• **Converted Leads**: {converted_leads}\n"
                result += f"• **Overall Conversion Rate**: {conversion_rate:.1f}%\n"
                result += f"• **Total Revenue**: ${total_revenue:,.0f}\n"
                result += f"• **Average Deal Size**: ${avg_deal_size:,.0f}\n"
                result += f"• **Average Lead Score**: {avg_lead_score:.1f}\n"
                return result
            
            else:
                return "I couldn't understand your question. Please try rephrasing it or use one of the example questions below. I can help you analyze platforms, industries, company sizes, lead scores, conversion rates, and revenue data."
                
        except Exception as e:
            return f"Sorry, I encountered an error processing your question: {str(e)}. Please try a different question."
    
    # QueryChat response handler
    @output
    @render.ui
    def query_response():
        # Only show response after button is clicked
        if input.submit_query() == 0:
            return ui.div()
        
        question = input.query_question()
        if not question or question.strip() == "":
            return ui.div(
                ui.h4("Please enter a question", style="color: #e74c3c;"),
                class_="chat-response"
            )
        
        try:
            answer = process_natural_language_query(question)
            return ui.div(
                ui.h4(f"Q: {question}", style="color: #2c3e50; margin-bottom: 15px;"),
                ui.markdown(answer),
                class_="chat-response"
            )
        except Exception as e:
            return ui.div(
                ui.h4(f"Q: {question}", style="color: #2c3e50; margin-bottom: 15px;"),
                ui.p(f"Sorry, I encountered an error: {str(e)}", style="color: #e74c3c;"),
                class_="chat-response"
            )

# Create the app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()