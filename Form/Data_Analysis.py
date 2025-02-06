import pandas as pd
import matplotlib.pyplot as plt
import glob
from scipy import stats
import numpy as np
# Step 1: Read all CSV files into a single DataFrame
csv_files = glob.glob(r"C:\Users\7000040643\Code\recoAgent\Form\*.csv")  # Adjust the path accordingly
dataframes = [pd.read_csv(file) for file in csv_files]
combined_df = pd.concat(dataframes, ignore_index=True)

# Step 2: Convert 'Known' column to numeric (True=1, False=0)
combined_df['Known'] = combined_df['Known'].astype(int)
combined_df['Like'] = combined_df['Like'].astype(int)
combined_df['Source'] = combined_df['Source'].replace('Unkwown List', 'Far from you')
combined_df['Source'] = combined_df['Source'].replace('Known List', 'Near to you')
# Step 3: Calculate averages for each source
averages = combined_df.groupby('Source')['Known'].mean()
averages_l = combined_df.groupby('Source')['Like'].mean()
# Step 4: Perform the t-test
known_known_list = combined_df[combined_df['Source'] == 'Near to you']['Known']
known_unknown_list = combined_df[combined_df['Source'] == 'Far from you']['Known']
t_statistic, p_value = stats.ttest_ind(known_known_list, known_unknown_list, equal_var=False)

# T-test Likes
likes_k = combined_df[combined_df['Source'] == 'Near to you']['Like']
likes_u = combined_df[combined_df['Source'] == 'Far from you']['Like']
t_statistic, p_value_l = stats.ttest_ind(likes_k, likes_u, equal_var=False)

# Step 5: Plot the averages
plt.figure(figsize=(10, 6))
bar_colors = ['skyblue', 'lightgreen']
averages.plot(kind='bar', color=bar_colors, alpha=0.7)

# Step 6: Get the y-values for the horizontal line
y1 = averages.iloc[0]  # Average for Known_list
y2 = averages.iloc[1]  # Average for Unknown_list
y_avg = max(y1, y2) + 0.05  # Set the y-coordinate slightly above the max average

# Step 7: Draw a horizontal line connecting the tops of the bars
plt.plot([0, 1], [y_avg, y_avg], color='red', linestyle='--', linewidth=1)

# Step 8: Draw vertical lines from the horizontal line to the tops of the bars
plt.plot([0, 0], [y_avg, y1], color='red', linestyle='--', linewidth=1)
plt.plot([1, 1], [y_avg, y2], color='red', linestyle='--', linewidth=1)

# Step 9: Annotate the p-value
mid_x = (0 + 1) / 2  # Midpoint between the two bars
plt.text(mid_x, y_avg + 0.05, f'pvalue<0.001', color='red', ha='center', fontsize=8)

# Step 10: Customize the plot
plt.ylabel('Average')
plt.xticks(rotation=0)
plt.ylim(0, y_avg + 0.1)  # Set y-axis limits to show averages and lines
plt.show()

# Plots likes
plt.figure(figsize=(10, 6))
bar_colors = ['skyblue', 'lightgreen']
averages_l.plot(kind='bar', color=bar_colors, alpha=0.7)

# Step 6: Get the y-values for the horizontal line
y1 = averages_l.iloc[0]  # Average for Known_list
y2 = averages_l.iloc[1]  # Average for Unknown_list
y_avg = max(y1, y2) + 0.05  # Set the y-coordinate slightly above the max average

# Step 7: Draw a horizontal line connecting the tops of the bars
plt.plot([0, 1], [y_avg, y_avg], color='red', linestyle='--', linewidth=1)

# Step 8: Draw vertical lines from the horizontal line to the tops of the bars
plt.plot([0, 0], [y_avg, y1], color='red', linestyle='--', linewidth=1)
plt.plot([1, 1], [y_avg, y2], color='red', linestyle='--', linewidth=1)

# Step 9: Annotate the p-value
mid_x = (0 + 1) / 2  # Midpoint between the two bars
plt.text(mid_x, y_avg + 0.05, f'pvalue={p_value_l:.4f}', color='red', ha='center', fontsize=8)

# Step 10: Customize the plot
plt.ylabel('Average Like')
plt.xticks(rotation=0)
plt.ylim(0, y_avg + 0.1)  # Set y-axis limits to show averages and lines
plt.show()