import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import StrMethodFormatter
from matplotlib.offsetbox import OffsetImage, AnnotationBbox



def get_transfer_history(page):
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; {Android Version}; {Build Tag etc.}) AppleWebKit/{WebKit Rev} ('
                             'KHTML, like Gecko) Chrome/{Chrome Rev} Mobile Safari/{WebKit Rev}'}
    tree = requests.get(page, headers=headers)
    site_html = BeautifulSoup(tree.text, 'html.parser')

    # Pulling Table Headers Text to identify transfers by year
    table_headers = site_html.find_all('h2')
    table_header_texts = []
    for table_header in table_headers:
        table_header_texts.append(table_header.text)
        

    # Pulling all tbody tags where transfer info is held in rows

    tbodies = site_html.find_all('tbody')

    # Pruning tbodies and table_headers to only look at transfers post 2000

    table_header_texts = table_header_texts[4:46]
    tbodies = tbodies[1:43]

    players = []
    transfer_fees = []
    transfer_windows = []
    player_links = []

    #Pulling all transfer data per row in each Tbody, along with the relevant Table Header so that I know when the player was bought/sold

    for tbody in tbodies:

        rows = tbody.find_all('tr')

        x = tbodies.index(tbody)

        for row in rows:
            player = row.find('td', {'class': 'hauptlink'})
            players.append(player.text)
            transfer_fee = row.find('td', {'class': 'rechts'})
            player_link = row.find('a', {'class' : 'spielprofil_tooltip'})
            player_link = player_link.get('href')
            player_links.append('https://www.transfermarkt.us{}'.format(player_link))
            transfer_fees.append(transfer_fee)
            transfer_windows.append(table_header_texts[x])

    data = {'players': players,'player_links' : player_links, 'transfer_fees': transfer_fees, 'transfer_window': transfer_windows}
    team_data = pd.DataFrame(data=data)
    return team_data


man_united = get_transfer_history('https://www.transfermarkt.us/manchester-united/alletransfers/verein/985')



#Function to clean the dataframe to make plotting possible

def clean_df(df, team_name):

    df['players'] = df['players'].str.strip('\n')

    df['arrival'] = np.where(df['transfer_window'].str.contains('Arrivals'), 1, 0)

    df['transfer_window'] = df['transfer_window'].str.extract(r'(\d{2}/\d{2})')

    # Replacing 'M' and 'th' symbols with the appropriate amount of zeros, extracting all digits, replacing nulls with zeros, and dividing by 1 million to scale fees down
    df['transfer_fees'] = df['transfer_fees'].astype(str).str.replace('m', '0000')
    df['transfer_fees'] = df['transfer_fees'].str.replace('th', '000')
    df['transfer_fees'] = df['transfer_fees'].str.findall('(\d)')
    df['transfer_fees'] = df['transfer_fees'].str.join('')

    df['transfer_fees'] = np.where(df['transfer_fees'] == "", 0, df['transfer_fees'])
    df['transfer_fees'] = np.where(df['transfer_fees'] == np.NAN, 0, df['transfer_fees'])
    df['transfer_fees'] = df['transfer_fees'].astype(int)
    df['transfer_fees'] = df['transfer_fees']/1000000

    # If we were to calculate net spend, a popular method to compare transfer business amongst soccer teams, departures would decrease net spend, so we will make the values negative


    df['transfer_fees'] = np.where(df['arrival'] == 0, -(df['transfer_fees']), df['transfer_fees'])

    #Adding in a column for the team name so that we can append the data from other teams for a complete dataset of team transfer activity

    df['team'] = "{}".format(team_name)


clean_df(man_united, team_name='Man_United')

#Filtering the dataset to get the most expensive arrival per season

arrivals = man_united[man_united['arrival'] == 1]
Highest_Arrival_Transfers = arrivals.groupby(['transfer_window'])['transfer_fees'].transform(max) == arrivals['transfer_fees']
Highest_Arrival_Transfers = arrivals[Highest_Arrival_Transfers]

highest_arrival_transfer_links = Highest_Arrival_Transfers['player_links'].tolist()
highest_arrival_transfer_players = Highest_Arrival_Transfers['players'].tolist()


#Pulling the image for each of these players to plot

for link in highest_arrival_transfer_links:
    i = highest_arrival_transfer_links.index(link)
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; {Android Version}; {Build Tag etc.}) AppleWebKit/{WebKit Rev} ('
                             'KHTML, like Gecko) Chrome/{Chrome Rev} Mobile Safari/{WebKit Rev}'}
    page = requests.get(link, headers=headers)
    html = BeautifulSoup(page.text, 'html.parser')
    img_link = html.find_all('img', {'title' : highest_arrival_transfer_players[i]})
    img = img_link[0].get('src').split("?lm")[0]

    with open(r'C:\Users\harwc\PycharmProjects\EPL_Transfer_Scraping\Player Images\{}.jpg'.format(highest_arrival_transfer_players[i]), "wb") as f:
        f.write(requests.get(img).content)


# Pictures are scraped as squares which don't look very good when plotted. Making them circular for a better looking graph.


def CircularizerImage(FolderPath, ImageName):

    img = Image.open(str(FolderPath)+str(ImageName)).convert('RGB')
    NpImg = np.array(img)
    h, w = img.size

    circle_layer = Image.new(mode='L', size=img.size, color=0)
    circle = ImageDraw.Draw(circle_layer)
    circle.pieslice([0, 0, h, w], 0, 360, fill=255)

    NpCircle = np.array(circle_layer)
    NpImage = np.dstack((NpImg, NpCircle))

    Player_Name = ImageName.strip('.jpg')
    Image.fromarray(NpImage).save('C:/Users/harwc/PycharmProjects/EPL_Transfer_Scraping/Circular_Player_Images/{}.png'.format(Player_Name))

files = os.listdir(r'C:\Users\harwc\PycharmProjects\EPL_Transfer_Scraping\Player Images')


for file in files:
    CircularizerImage('C:/Users/harwc/PycharmProjects/EPL_Transfer_Scraping/Player Images/', file)

# Adding an integer year value so that I can plot the season/years on the x-axis. I'm also filtering to only transfers after 2009, for a more concise graph.
# I'm also filtering the players by alphabetical order so that the correct images are added to the respective row.

years = (range(2021, 2000, -1))
Highest_Arrival_Transfers['years'] = years
Highest_Arrival_Transfers = Highest_Arrival_Transfers.sort_values(by='players')

CircularizedImages = os.listdir(r'C:\Users\harwc\PycharmProjects\EPL_Transfer_Scraping\Circular_Player_Images')
Highest_Arrival_Transfers['ImagePath'] = CircularizedImages
os.chdir(r'C:\Users\harwc\PycharmProjects\EPL_Transfer_Scraping\Circular_Player_Images')


Highest_Transfers_In_2010s = Highest_Arrival_Transfers[Highest_Arrival_Transfers['years'] > 2009]
Highest_Transfers_In_2010s = Highest_Transfers_In_2010s.sort_values(by='years')

transfer_fees = Highest_Transfers_In_2010s['transfer_fees'].tolist()
years = Highest_Transfers_In_2010s['years'].tolist()
xticks = Highest_Transfers_In_2010s['transfer_window'].tolist()
player_names = Highest_Transfers_In_2010s['players'].tolist()
player_images = Highest_Transfers_In_2010s['ImagePath'].tolist()

def GetImage(path):
    return OffsetImage(plt.imread(path), zoom=.30)


matplotlib.style.use('seaborn')
fig, ax = plt.subplots()
plt.plot(years, transfer_fees, linewidth=1, color='red')
plt.gcf().set_size_inches(20,25)
plt.xticks(ticks = np.arange(min(years), max(years)+1, 1),labels=xticks)
plt.title('Manchester United\'s Most Expensive Purchases By Season', fontsize=25, ha='center')
plt.ylabel('Transfer Fee', fontsize=15)
plt.xlabel('Season', fontsize=15)
plt.gca().yaxis.set_major_formatter(StrMethodFormatter("${x:,.0f}M"))

for transfer_fee, year, player_image in zip(transfer_fees, years, player_images):

    ab = AnnotationBbox(GetImage(player_image), (year, transfer_fee), frameon=False)
    ax.add_artist(ab)

for x, player in enumerate(player_names):
    if player == player_names[1]:
        ax.annotate(player_names[1], (years[1], transfer_fees[1]), textcoords='offset points', xytext=(0, 30),
                    ha='center')
    else:
        ax.annotate(player, (years[x], transfer_fees[x]),textcoords='offset points', xytext=(0,-40), ha='center')



plt.show()