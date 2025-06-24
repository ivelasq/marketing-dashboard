import chatlas
import great_tables as gt
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from plotly.subplots import make_subplots
from shiny import reactive
from shiny.express import input, render, ui
from shinywidgets import render_plotly
import querychat as qc

plotly_modebar_remove = ["zoom", "pan", "lasso", "select", "autoscale"]


def use_github_models(system_prompt: str) -> chatlas.Chat:
    return chatlas.ChatGithub(
        model="gpt-4.1",
        system_prompt=system_prompt,
    )

def use_anthropic_models(system_prompt: str) -> chatlas.Chat:
    return chatlas.ChatAnthropic(
        model="claude-3-7-sonnet-latest",
        system_prompt=system_prompt,
    )


def load_data():
    leads_df = pl.read_csv("salesforce_leads.csv")
    platform_df = pl.read_csv("platform_performance.csv")
    quality_df = pl.read_csv("lead_quality_metrics.csv")

    # Convert date columns
    leads_df = leads_df.with_columns([
        pl.col("created_date").str.to_date("%Y-%m-%d"),
        pl.col("conversion_date").str.to_date("%Y-%m-%d"),
    ])

    # Add company size categories
    leads_df = leads_df.with_columns(
        pl.when(pl.col("employees") < 50)
        .then(pl.lit("Small (< 50)"))
        .when(pl.col("employees") <= 250)
        .then(pl.lit("Medium (50-250)"))
        .when(pl.col("employees") <= 500)
        .then(pl.lit("Large (251-500)"))
        .otherwise(pl.lit("Enterprise (500+)"))
        .alias("company_size")
    )

    return leads_df, platform_df, quality_df


leads_df, platform_df, quality_df = load_data()

ui.page_opts(
    title="Marketing Team",
)


@reactive.calc
def filtered_data():
    # Apply filters
    filtered_leads = leads_df

    # Date filter
    date_start, date_end = input.date_range()
    filtered_leads = filtered_leads.filter(
        (pl.col("created_date") >= pl.lit(date_start))
        & (pl.col("created_date") <= pl.lit(date_end))
    )

    # Platform filter
    if input.platforms():
        filtered_leads = filtered_leads.filter(
            pl.col("platform").is_in(input.platforms())
        )

    # Company size filter
    if input.company_sizes():
        filtered_leads = filtered_leads.filter(
            pl.col("company_size").is_in(input.company_sizes())
        )

    # Industry filter
    if input.industries():
        filtered_leads = filtered_leads.filter(
            pl.col("industry").is_in(input.industries())
        )

    # Status filter
    if input.lead_status():
        filtered_leads = filtered_leads.filter(
            pl.col("status").is_in(input.lead_status())
        )

    return {
        "leads": filtered_leads,
        "platform": platform_df,
        "quality": quality_df,
    }


@reactive.calc
def trend_data():
    filtered_leads = filtered_data()["leads"]

    # Group by month and platform
    df = (
        filtered_leads.with_columns(
            pl.col("created_date").dt.strftime("%Y-%m").alias("month")
        )
        .group_by(["month", "platform"])
        .agg(pl.len().alias("leads"))
        .sort(["month", "platform"])
    )

    if len(df) == 0:
        return ui.div("No data available")

    else:
        return df


@reactive.calc
def platform_stats():
    filtered_leads = filtered_data()["leads"]

    # Platform performance metrics
    platform_stats = filtered_leads.group_by("platform").agg([
        pl.col("lead_score").mean().alias("avg_lead_score"),
        (pl.col("status").eq("Converted").sum() / pl.len() * 100).alias(
            "conversion_rate"
        ),
    ])

    if len(platform_stats) == 0:
        return ui.div("No data available")

    else:
        return platform_stats


@reactive.calc
def funnel_data():
    filtered_leads = filtered_data()["leads"]

    # Conversion funnel by platform
    funnel_data = []
    for platform in filtered_leads["platform"].unique().to_list():
        platform_leads = filtered_leads.filter(pl.col("platform") == platform)
        total = platform_leads.height
        qualified = platform_leads.filter(
            pl.col("status").is_in(["Qualified", "Opportunity", "Converted"])
        ).height
        converted = platform_leads.filter(
            pl.col("status") == "Converted"
        ).height

        funnel_data.extend([
            {"platform": platform, "stage": "Total Leads", "count": total},
            {"platform": platform, "stage": "Qualified", "count": qualified},
            {"platform": platform, "stage": "Converted", "count": converted},
        ])

    funnel_df = pl.DataFrame(funnel_data)

    if len(funnel_df) == 0:
        return ui.div("No data available")
    else:
        return funnel_df


@reactive.calc
def industry_stats():
    filtered_leads = filtered_data()["leads"]

    # Industry performance
    industry_stats = (
        filtered_leads.group_by("industry")
        .agg([
            pl.len().alias("lead_count"),
            pl.col("lead_score").mean().alias("avg_lead_score"),
            (pl.col("status").eq("Converted").sum() / pl.len() * 100).alias(
                "conversion_rate"
            ),
        ])
        .filter(pl.col("lead_count") >= 2)
    )

    if len(industry_stats) == 0:
        return ui.div("No data available")
    else:
        return industry_stats


@reactive.calc
def revenue_data():
    filtered_leads = filtered_data()["leads"]

    # Revenue by platform and company size
    revenue_data = (
        filtered_leads.filter(pl.col("status") == "Converted")
        .group_by(["platform", "company_size"])
        .agg(pl.col("opportunity_value").sum().alias("revenue"))
    )

    if len(revenue_data) == 0:
        return ui.div("No data available")
    else:
        return revenue_data


with ui.nav_panel("Dashboard"):
    ui.h1("Lead Quality Dashboard")

    with ui.layout_sidebar():
        with ui.sidebar(width=300, bg="#f8f8f8"):
            ui.input_date_range(
                "date_range",
                "Date Range",
                start="2024-01-01",
                end="2024-06-30",
                min="2024-01-01",
                max="2024-12-31",
            )

            ui.input_checkbox_group(
                "platforms",
                "Platforms",
                choices=[
                    "LinkedIn",
                    "TikTok",
                    "Events",
                    "Google Ads",
                    "Facebook",
                    "YouTube",
                    "Webinars",
                    "Podcasts",
                ],
                selected=[
                    "LinkedIn",
                    "TikTok",
                    "Events",
                    "Google Ads",
                    "Facebook",
                    "YouTube",
                    "Webinars",
                    "Podcasts",
                ],
            )

            ui.input_checkbox_group(
                "company_sizes",
                "Company Size",
                choices=[
                    "Small (< 50)",
                    "Medium (50-250)",
                    "Large (251-500)",
                    "Enterprise (500+)",
                ],
                selected=[
                    "Small (< 50)",
                    "Medium (50-250)",
                    "Large (251-500)",
                    "Enterprise (500+)",
                ],
            )

            ui.input_checkbox_group(
                "lead_status",
                "Lead Status",
                choices=["Converted", "Qualified", "Opportunity", "Nurturing"],
                selected=[
                    "Converted",
                    "Qualified",
                    "Opportunity",
                    "Nurturing",
                ],
            )

            ui.input_selectize(
                "industries",
                "Industries",
                choices=leads_df["industry"].unique().sort().to_list(),
                selected=[],
                multiple=True,
            )

            @render.download(label="Download CSV")
            def download1():
                pass

        with ui.layout_column_wrap():
            with ui.value_box():
                "Total Leads"

                @render.ui
                def kpi_total_leads():
                    filtered_leads = filtered_data()["leads"]
                    total_leads = filtered_leads.height
                    return total_leads

            with ui.value_box():
                "Conversion Rate"

                @render.ui
                def kpi_conversion_rate():
                    filtered_leads = filtered_data()["leads"]
                    conversion_rate = (
                        filtered_leads.filter(
                            pl.col("status") == "Converted"
                        ).height
                        / filtered_leads.height
                    ) * 100
                    return conversion_rate

            with ui.value_box():
                "Ave Deal Size"

                @render.ui
                def kpi_avg_deal_size():
                    filtered_leads = filtered_data()["leads"]
                    converted_leads = filtered_leads.filter(
                        pl.col("status") == "Converted"
                    )
                    avg_deal = converted_leads["opportunity_value"].mean()
                    return f"${avg_deal:,.0f}"

            with ui.value_box():
                "Total Revenue"

                @render.ui
                def kpi_total_revenue():
                    filtered_leads = filtered_data()["leads"]
                    converted_leads = filtered_leads.filter(
                        pl.col("status") == "Converted"
                    )
                    total_revenue = converted_leads["opportunity_value"].sum()
                    return f"${total_revenue:,.0f}"

        with ui.layout_column_wrap():

            @render_plotly
            def leads_trend_chart():
                fig = px.line(
                    trend_data(),
                    x="month",
                    y="leads",
                    color="platform",
                    markers=True,
                    title="Lead Generation Trends by Platform",
                    labels={
                        "month": "Month",
                        "leads": "Number of Leads",
                        "platform": "Platform",
                    },
                )

                # Calculate global y-axis range to maintain consistency
                y_max = trend_data()["leads"].max() * 1.1  # Add 10% padding

                fig.update_layout(
                    hovermode="x unified",
                    plot_bgcolor="white",
                    modebar_remove=plotly_modebar_remove,
                    yaxis=dict(
                        range=[0, y_max],  # Set fixed y-axis range
                        fixedrange=True,  # Prevent y-axis from auto-adjusting
                    ),
                )

                fig.update_traces(
                    hovertemplate="Leads: %{y}",
                    customdata=trend_data()["platform"],
                )

                return fig

            @render_plotly
            def platform_performance_chart():
                # Create a figure with secondary y-axis
                fig = make_subplots(specs=[[{"secondary_y": True}]])

                # Add bar chart for lead score
                fig.add_trace(
                    go.Bar(
                        x=platform_stats()["platform"],
                        y=platform_stats()["avg_lead_score"],
                        name="Average Lead Score",
                        opacity=0.8,
                        hovertemplate="<b>%{x}</b><br>Avg Lead Score: %{y:.1f}<extra></extra>",
                    ),
                    secondary_y=False,
                )

                # Add line and points for conversion rate
                fig.add_trace(
                    go.Scatter(
                        x=platform_stats()["platform"],
                        y=platform_stats()["conversion_rate"],
                        mode="lines+markers",
                        name="Conversion Rate (%)",
                        hovertemplate="<b>%{x}</b><br>Conversion Rate: %{y:.1f}%<extra></extra>",
                    ),
                    secondary_y=True,
                )

                # Set axis titles and layout properties
                fig.update_layout(
                    title={
                        "text": "Platform Performance: Lead Score vs Conversion Rate",
                    },
                    plot_bgcolor="white",
                    hoverlabel=dict(bgcolor="white", font_size=12),
                    modebar_remove=plotly_modebar_remove,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=0.95,
                        xanchor="center",
                        x=0.5,
                    ),
                )

                # Update axes
                fig.update_xaxes(
                    title_text="Platform",
                    title_font=dict(size=12, color="#64748b"),
                    tickfont=dict(size=10),
                    gridcolor="#f1f5f9",
                )

                fig.update_yaxes(
                    title_text="Average Lead Score",
                    title_font=dict(size=12, color="#64748b"),
                    tickfont=dict(size=10),
                    gridcolor="#f1f5f9",
                    secondary_y=False,
                )

                fig.update_yaxes(
                    title_text="Conversion Rate (%)",
                    title_font=dict(size=12, color="#64748b"),
                    tickfont=dict(size=10),
                    gridcolor="#f1f5f9",
                    secondary_y=True,
                )

                # Fix y-axis ranges to prevent jumping when interacting
                y1_max = platform_stats()["avg_lead_score"].max() * 1.1
                y2_max = platform_stats()["conversion_rate"].max() * 1.1

                fig.update_yaxes(range=[0, y1_max], secondary_y=False)
                fig.update_yaxes(range=[0, y2_max], secondary_y=True)

                return fig

        with ui.layout_column_wrap():

            @render_plotly
            def conversion_funnel_chart():
                fig = px.bar(
                    funnel_data(),
                    x="stage",
                    y="count",
                    color="platform",
                    barmode="group",
                    title="Conversion Funnel by Platform",
                    labels={
                        "stage": "Stage",
                        "count": "Number of Leads",
                        "platform": "Platform",
                    },
                )

                fig.update_layout(
                    plot_bgcolor="white",
                    modebar_remove=plotly_modebar_remove,
                )

                # Add hover template for better information display
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>Platform: %{fullData.name}<br>Count: %{y}<extra></extra>"
                )

                return fig

            @render_plotly
            def lead_score_distribution():
                fig = px.histogram(
                    filtered_data()["leads"],
                    x="lead_score",
                    color="platform",
                    nbins=20,  # Equivalent to bins=20 in ggplot
                    opacity=0.8,  # Equivalent to alpha=0.8
                    barmode="overlay",  # Equivalent to position='identity'
                    title="Lead Score Distribution by Platform",
                    labels={
                        "lead_score": "Lead Score",
                        "count": "Count",
                        "platform": "Platform",
                    },
                )

                # Update layout to match the ggplot styling
                fig.update_layout(
                    modebar_remove=plotly_modebar_remove,
                    plot_bgcolor="white",
                )

                # Add hover template for better information display
                fig.update_traces(
                    hovertemplate="<b>Lead Score: %{x}</b><br>Platform: %{fullData.name}<br>Count: %{y}<extra></extra>"
                )

                return fig

        @render_plotly
        def industry_performance_chart():
            fig = px.scatter(
                industry_stats(),
                x="avg_lead_score",
                y="conversion_rate",
                size="lead_count",
                opacity=0.8,
                title="Industry Performance: Lead Score vs Conversion Rate",
                labels={
                    "avg_lead_score": "Average Lead Score",
                    "conversion_rate": "Conversion Rate (%)",
                    "lead_count": "Lead Count",
                },
            )

            # Update layout to match the ggplot styling
            fig.update_layout(
                modebar_remove=plotly_modebar_remove,
                plot_bgcolor="white",
            )

            # Improve hover information
            fig.update_traces(
                hovertemplate=(
                    ""
                    + "Average Lead Score: %{x:.1f}<br>"
                    + "Conversion Rate: %{y:.1f}%<br>"
                    + "Lead Count: %{marker.size}<extra></extra>"
                )
            )

            return fig

        @render_plotly
        def revenue_analysis_chart():
            fig = px.bar(
                revenue_data(),
                x="company_size",
                y="revenue",
                color="platform",
                barmode="group",  # Equivalent to position='dodge' in ggplot
                title="Revenue by Company Size and Platform",
                labels={
                    "company_size": "Company Size",
                    "revenue": "Revenue ($)",
                    "platform": "Platform",
                },
            )

            # Update layout to match the ggplot styling
            fig.update_layout(
                modebar_remove=plotly_modebar_remove,
                plot_bgcolor="white",
                xaxis=dict(),
                yaxis=dict(),
            )

            # Add hover template for better information display
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br>Platform: %{fullData.name}<br>Revenue: $%{y:,.0f}<extra></extra>"
            )

            return fig


with ui.nav_panel("FAQ"):

    @reactive.calc
    def by_conversion_rate():
        conversion_rate = (
            leads_df.group_by("platform")
            .agg([
                pl.len().alias("total"),
                (pl.col("status") == "Converted").sum().alias("converted"),
            ])
            .with_columns(
                (pl.col("converted").cast(pl.Float64) / pl.col("total")).alias(
                    "conversion_rate"
                )
            )
            .sort("conversion_rate", descending=True)
        )
        return conversion_rate

    @reactive.calc
    def by_average_lead_score():
        lead_score = (
            leads_df.group_by("platform")
            .agg([
                pl.col("lead_score").mean().alias("avg_lead_score"),
                pl.len().alias("total_leads"),
            ])
            .sort("avg_lead_score", descending=True)
        )
        return lead_score

    with ui.accordion(id="faq", multiple=True, open=False):
        with ui.accordion_panel(
            title="Which platform generates the highest quality leads?",
        ):
            "Define high quality leads by conversion rates"

            with ui.layout_column_wrap():
                with ui.card():

                    @render.data_frame
                    def show_highest_conversion_rate():
                        return by_conversion_rate()

                with ui.card():

                    @render_plotly
                    def plot_highest_conversion_rate():
                        df_plot = by_conversion_rate().to_pandas()

                        # Create the bar chart
                        fig = px.bar(
                            df_plot,
                            x="platform",
                            y="conversion_rate",
                            title="Platform Conversion Rates - Highest Quality Leads",
                            labels={
                                "conversion_rate": "Conversion Rate",
                                "platform": "Platform",
                            },
                            text="conversion_rate",  # Show values on bars
                        )

                        # Customize the chart
                        fig.update_traces(
                            texttemplate="%{text:.1%}",  # Format as percentage
                            textposition="outside",
                        )

                        fig.update_layout(
                            yaxis_tickformat=".1%",  # Format y-axis as percentage
                            xaxis_title="Platform",
                            yaxis_title="Conversion Rate",
                            showlegend=False,
                            height=500,
                        )

                        # Alternative with more customization using graph_objects
                        fig_custom = go.Figure(
                            data=[
                                go.Bar(
                                    x=df_plot["platform"],
                                    y=df_plot["conversion_rate"],
                                    text=[
                                        f"{rate:.1%}"
                                        for rate in df_plot["conversion_rate"]
                                    ],
                                    textposition="outside",
                                    marker_color="lightblue",
                                    marker_line_color="darkblue",
                                    marker_line_width=1.5,
                                )
                            ]
                        )

                        fig_custom.update_layout(
                            title="Platform Conversion Rates - Highest Quality Leads",
                            xaxis_title="Platform",
                            yaxis_title="Conversion Rate",
                            yaxis_tickformat=".1%",
                            height=500,
                            template="plotly_white",
                        )

                        return fig

            "Define quality leads by average lead score"

            with ui.layout_column_wrap():
                with ui.card():

                    @render.data_frame
                    def show_average_lead_score():
                        return by_average_lead_score()

                with ui.card():

                    @render_plotly
                    def plot_average_lead_score():
                        fig_score = px.bar(
                            by_average_lead_score(),
                            x='platform',
                            y='avg_lead_score',
                            title='Average Lead Score by Platform - Highest Quality Leads',
                            labels={
                                'avg_lead_score': 'Average Lead Score',
                                'platform': 'Platform'
                            },
                            text='avg_lead_score',
                            color='avg_lead_score',
                            color_continuous_scale='Blues'
                        )

                        fig_score.update_traces(
                            texttemplate='%{text:.1f}',
                            textposition='outside'
                        )

                        fig_score.update_layout(
                            xaxis_title='Platform',
                            yaxis_title='Average Lead Score',
                            showlegend=False,
                            height=500
                        )
                        return fig_score


        with ui.accordion_panel(
            "Which company size segment has the highest revenue potential?"
        ):

            @reactive.calc
            def revenue_potential():
                rev_pot = (
                    leads_df
                    .group_by("company_size")
                    .agg(
                        pl.col("opportunity_value").sum().alias("total_revenue_potential")
                    )
                    .sort("total_revenue_potential", descending=True)
                )
                return rev_pot

            with ui.layout_column_wrap():
                with ui.card():
                    @render.data_frame
                    def show_revenue_potential():
                        formatted_results = revenue_potential().with_columns(
                            pl.col("total_revenue_potential").map_elements(
                                lambda x: f"${x:,.0f}",
                                return_dtype=pl.Utf8
                            ).alias("formatted_revenue")
                        )
                        return formatted_results

                with ui.card():
                    @render_plotly
                    def plot_revenue_potential():
                        fig = px.bar(
                            revenue_potential(),
                            x='total_revenue_potential',
                            y='company_size',
                            orientation='h',
                            title='Total Revenue Potential by Company Size',
                            labels={
                                'total_revenue_potential': 'Total Revenue Potential ($)',
                                'company_size': 'Company Size'
                            },
                            text='total_revenue_potential',
                            color='total_revenue_potential',
                            color_continuous_scale='Blues',
                            category_orders={'company_size': revenue_potential()['company_size']}
                        )

                        fig.update_traces(
                            texttemplate='$%{text:,.0f}',
                            textposition='inside'
                        )

                        fig.update_layout(
                            xaxis_tickformat='$,.0f',
                            xaxis_title='Total Revenue Potential ($)',
                            yaxis_title='Company Size',
                            height=500,
                            showlegend=False,
                            coloraxis_showscale=False ,
                            margin=dict(r=100),
                        )

                        return fig

        with ui.accordion_panel(
            "What are the characteristics of our best converting leads?"
        ):
            "Define best converted leads as leads cores in the top quantile (top 25%)"

            @render.data_frame
            def best_lead_characteristics():

                # Step 1: Filter converted leads and find 75th percentile threshold
                converted_leads = leads_df.filter(pl.col("status") == "Converted")

                score_p75 = converted_leads.select(
                    pl.col("lead_score").quantile(0.75).alias("score_p75")
                ).item()

                # Step 2: Filter high score converted leads
                high_score_converted = converted_leads.filter(
                    pl.col("lead_score") >= score_p75
                )

                # Step 3: Get most common values for categorical columns
                top_platform = (
                    high_score_converted
                    .group_by("platform")
                    .agg(pl.len().alias("count"))
                    .sort("count", descending=True)
                    .limit(1)
                    .select("platform")
                    .item()
                )

                top_industry = (
                    high_score_converted
                    .group_by("industry")
                    .agg(pl.len().alias("count"))
                    .sort("count", descending=True)
                    .limit(1)
                    .select("industry")
                    .item()
                )

                top_company_size = (
                    high_score_converted
                    .group_by("company_size")
                    .agg(pl.len().alias("count"))
                    .sort("count", descending=True)
                    .limit(1)
                    .select("company_size")
                    .item()
                )

                # Step 4: Calculate individual metrics
                lead_count = high_score_converted.height
                avg_opportunity_value = high_score_converted.select(pl.col("opportunity_value").mean()).item()
                avg_employees = high_score_converted.select(pl.col("employees").mean()).item()
                avg_annual_revenue = high_score_converted.select(pl.col("annual_revenue").mean()).item()

                # Step 5: Create long format report table
                report_data = [
                    ("Lead Score Threshold (75th Percentile)", f"{score_p75:.1f}"),
                    ("Total High Score Converted Leads", f"{lead_count:,}"),
                    ("Top Platform", top_platform),
                    ("Top Industry", top_industry),
                    ("Top Company Size", top_company_size),
                    ("Average Opportunity Value", f"${avg_opportunity_value:,.0f}"),
                    ("Average Employees", f"{avg_employees:,.0f}"),
                    ("Average Annual Revenue", f"${avg_annual_revenue:,.0f}")
                ]

                # Create the long format table
                report_table = pl.DataFrame({
                    "Metric": [item[0] for item in report_data],
                    "Value": [item[1] for item in report_data]
                })

                return report_table


        with ui.accordion_panel(
            "What are the seasonal trends in lead generation?"
        ):
            @render_plotly
            def monthly_leads_source():
                leads_monthly = (
                    leads_df
                    .filter(pl.col("lead_source").is_not_null())
                    .with_columns([
                        pl.col("created_date").dt.strftime("%Y-%m").alias("month")
                    ])
                    .sort([
                        pl.col("month").reverse(),
                        pl.col("lead_source"),
                        pl.col("created_date").reverse()
                    ])
                )

                leads_summary = (
                    leads_monthly
                    .group_by(["month", "lead_source"])
                    .agg(pl.count().alias("lead_count"))
                    .sort(["month", "lead_source"])
                )

                fig = px.line(
                    leads_summary.to_pandas(),
                    x="month",
                    y="lead_count",
                    color="lead_source",
                    title="Lead Trends by Source Over Time",
                    labels={"lead_count": "Number of Leads", "month": "Month"},
                    markers=True
                )

                fig.update_layout(
                    hovermode="x unified",
                    xaxis_tickangle=-45,
                    plot_bgcolor="white"
                )

                fig.update_traces(
                    hovertemplate="%{fullData.name}: %{y} leads<extra></extra>"
                )
                return fig

with ui.nav_panel("Querychat"):
    querychat_config = qc.init(
        leads_df,
        "leads_df",
        create_chat_callback=use_anthropic_models,
    )

    with ui.layout_sidebar(fillable=True, fill=True):
        qc.sidebar("chat")

        chat = qc.server("chat", querychat_config)

        @render.data_frame
        def qc_data_table():
            return chat.df()
