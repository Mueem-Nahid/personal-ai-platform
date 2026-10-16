#set page(paper: "a4", margin: (x: 1.7cm, y: 1.5cm))
#set text(font: "New Computer Modern", size: 10.5pt)
#set par(justify: true, leading: 0.62em)
#set list(indent: 1em, spacing: 0.7em)

#align(center)[
  #text(size: 20pt, weight: "bold")[{{ profile.full_name|typst }}]
  #v(0.2em)
  {% if profile.title %}#text(size: 12pt, style: "italic")[{{ profile.title|typst }}]
  #v(0.2em){% endif %}
  #text(size: 9pt)[
    {%- if profile.email %}{{ profile.email|typst }}{% endif -%}
    {%- if profile.phone %} · {{ profile.phone|typst }}{% endif -%}
    {%- if profile.location %} · {{ profile.location|typst }}{% endif -%}
    {%- if profile.github_url %} · {{ profile.github_url|typst }}{% endif -%}
    {%- if profile.linkedin_url %} · {{ profile.linkedin_url|typst }}{% endif -%}
    {%- if profile.website %} · {{ profile.website|typst }}{% endif -%}
  ]
]

{% if job.title %}
#align(center)[#text(size: 9.5pt, style: "italic")[Target: {{ job.title|typst }}{% if job.company %} — {{ job.company|typst }}{% endif %}]]
{% endif %}

#v(0.6em)

{% if content.summary %}
= Summary

{{ content.summary|typst }}
{% endif %}

{% for section in content.sections %}
= {{ section.name|typst }}

{% for item in section.items %}
- {{ item|typst }}
{% endfor %}
{% endfor %}
