import os
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from .forms import DatasetUploadForm
from .analysis import (
    load_dataset,
    profile_dataset,
    clean_dataset,
    descriptive_statistics,
    build_bar_chart,
    detect_dataset_type,
    calculate_kpis,
    detect_trend,
    generate_ai_insights,
    detect_anomalies,
    forecast_next_period,
    generate_pdf_report,
    make_json_safe,
)


def upload_and_analyze(request):
    summary = None
    cleaning_report = None
    stats = None
    chart_html = None
    dataset_type = None
    kpis = None
    trend_chart_html = None
    trend_explanation = None
    ai_insights = None
    anomalies = None
    forecast = None
    error = None

    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            save_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            with open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            try:
                df = load_dataset(save_path)
                summary = profile_dataset(df)

                df, cleaning_report = clean_dataset(df)

                stats = descriptive_statistics(df)

                chart_html = build_bar_chart(df)

                dataset_type = detect_dataset_type(df)
                kpis = calculate_kpis(df, dataset_type)
                trend_chart_html, trend_explanation = detect_trend(df)

                ai_insights = generate_ai_insights(summary, stats, kpis, dataset_type)
                anomalies = detect_anomalies(df)
                forecast = forecast_next_period(df)

                request.session['report_context'] = make_json_safe({
                    'dataset_type': dataset_type,
                    'summary': summary,
                    'cleaning_report': cleaning_report,
                    'kpis': kpis,
                    'stats': stats,
                    'trend_explanation': trend_explanation,
                    'forecast': forecast,
                    'ai_insights': ai_insights,
                    'anomalies': anomalies,
                })

            except Exception as e:
                error = f"Couldn't read this file: {e}"
    else:
        form = DatasetUploadForm()

    return render(request, 'analyzer/upload.html', {
        'form': form,
        'summary': summary,
        'cleaning_report': cleaning_report,
        'stats': stats,
        'chart_html': chart_html,
        'dataset_type': dataset_type,
        'kpis': kpis,
        'trend_chart_html': trend_chart_html,
        'trend_explanation': trend_explanation,
        'ai_insights': ai_insights,
        'anomalies': anomalies,
        'forecast': forecast,
        'error': error,
    })


def download_pdf_report(request):
    context = request.session.get('report_context')
    if not context:
        return HttpResponse("No report available. Please analyze a file first.", status=400)

    pdf_buffer = generate_pdf_report(context)
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="data_analyst_report.pdf"'
    return response