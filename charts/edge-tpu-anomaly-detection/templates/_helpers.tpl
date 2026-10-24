{{/*
Expand the name of the chart.
*/}}
{{- define "edge-tpu-anomaly-detection.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "edge-tpu-anomaly-detection.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "edge-tpu-anomaly-detection.labels" -}}
helm.sh/chart: {{ include "edge-tpu-anomaly-detection.name" . }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "edge-tpu-anomaly-detection.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: edge-ml-infrastructure
{{- end }}

{{/*
Selector labels
*/}}
{{- define "edge-tpu-anomaly-detection.selectorLabels" -}}
app.kubernetes.io/name: {{ include "edge-tpu-anomaly-detection.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
