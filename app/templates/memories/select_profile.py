{% extends "base.html" %}

{% block title %}Select Profile | Remora{% endblock %}

{% block content %}
<div style="max-width: 1100px; margin: 0 auto; padding: 32px 20px 56px;">

    <!-- Header -->
    <div style="margin-bottom: 28px;">
        <a href="/ui/dashboard" style="
            text-decoration: none;
            color: #7d84a6;
            font-weight: 600;
            font-size: 14px;
        ">
            ← Back
        </a>

        <h1 style="
            margin: 12px 0 8px 0;
            font-size: 34px;
            line-height: 1.1;
            color: #2f355c;
        ">
            Who is this memory about?
        </h1>

        <p style="
            margin: 0;
            font-size: 16px;
            line-height: 1.6;
            color: #7d84a6;
        ">
            Choose the memorial profile where this memory should be saved.
        </p>
    </div>

    {% if profiles and profiles|length > 0 %}
        <div style="
            display: grid;
            grid-template-columns: repeat(2, minmax(280px, 1fr));
            gap: 22px;
        ">

            {% for profile in profiles %}
                <a href="/ui/memories/create?profile_id={{ profile.profile_id }}" style="
                    text-decoration: none;
                    color: inherit;
                    background: #ffffff;
                    border: 1px solid #e7e9f4;
                    border-radius: 28px;
                    padding: 26px 24px;
                    box-shadow: 0 10px 30px rgba(86, 97, 160, 0.08);
                    transition: transform 0.15s ease, box-shadow 0.15s ease;
                    display: block;
                "
                onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 14px 34px rgba(86, 97, 160, 0.12)'"
                onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 10px 30px rgba(86, 97, 160, 0.08)'"
                >

                    <!-- Avatar -->
                    <div style="
                        width: 64px;
                        height: 64px;
                        border-radius: 50%;
                        background: #eef0ff;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 26px;
                        margin-bottom: 18px;
                    ">
                        👤
                    </div>

                    <!-- Name -->
                    <div style="
                        font-size: 24px;
                        font-weight: 700;
                        color: #2f355c;
                        margin-bottom: 6px;
                    ">
                        {{ profile.full_name }}
                    </div>

                    <!-- Relationship -->
                    <div style="
                        font-size: 14px;
                        color: #8b90b3;
                        margin-bottom: 12px;
                    ">
                        {{ profile.relationship or "Memorial profile" }}
                    </div>

                    <!-- Description -->
                    {% if profile.short_description %}
                        <div style="
                            font-size: 15px;
                            color: #7d84a6;
                            line-height: 1.5;
                        ">
                            {{ profile.short_description }}
                        </div>
                    {% else %}
                        <div style="
                            font-size: 15px;
                            color: #b0b5d6;
                        ">
                            Select this profile to continue.
                        </div>
                    {% endif %}

                </a>
            {% endfor %}

        </div>

    {% else %}

        <!-- Empty State -->
        <div style="
            background: #ffffff;
            border-radius: 28px;
            padding: 32px;
            border: 1px solid #e7e9f4;
            box-shadow: 0 10px 30px rgba(86, 97, 160, 0.06);
            text-align: center;
        ">
            <div style="font-size: 48px; margin-bottom: 14px;">🕊️</div>

            <div style="
                font-size: 24px;
                font-weight: 700;
                color: #2f355c;
                margin-bottom: 10px;
            ">
                No profiles yet
            </div>

            <div style="
                font-size: 16px;
                color: #7d84a6;
                margin-bottom: 20px;
            ">
                Create a memorial profile first before adding a memory.
            </div>

            <a href="/ui/profiles/create" style="
                display: inline-block;
                padding: 12px 20px;
                border-radius: 16px;
                background: #5c63d6;
                color: #ffffff;
                text-decoration: none;
                font-weight: 600;
                box-shadow: 0 6px 18px rgba(92, 99, 214, 0.25);
            ">
                Create profile
            </a>
        </div>

    {% endif %}
</div>

<style>
    @media (max-width: 820px) {
        div[style*="grid-template-columns: repeat(2, minmax(280px, 1fr));"] {
            grid-template-columns: 1fr !important;
        }
    }
</style>

{% endblock %}
