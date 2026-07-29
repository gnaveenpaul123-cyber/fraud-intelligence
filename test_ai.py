from ai.ai_filter import analyze_scam

combined_text = """
I found a seller on Telegram.
He asked me to pay using UPI.
UPI ID: scammer@okaxis
Phone: 9876543210
After payment he blocked me.
"""

result = analyze_scam(combined_text)

print(result)