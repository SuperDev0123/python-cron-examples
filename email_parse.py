from datetime import datetime
import pytz


def email_parse(in_str):
    pre_order_str = "Just to confirm your job: "
    pre_date_str = "The date and time"
    order_index = in_str.find(pre_order_str)
    date_index = in_str.find(pre_date_str)

    order_extract_str = in_str[order_index + len(pre_order_str):]
    order_result = ""
    for m in order_extract_str:
        if not (m.isdigit() or m.isspace()):
            break;
        order_result = order_result + m

    order_arr = order_result.strip().split(' ')
    # new_result = re.findall('[0-9]+', order_extract_str)
    date_extract_str = in_str[date_index + len(pre_date_str):]
    index = 0
    for m in date_extract_str:
        if m.isdigit():
            break
        index = index + 1
    
    date_result = date_extract_str[index:]
    date_part = ""
    for m in date_result:
        if not (m.isdigit() or m.isspace() or m in ["/", ":"]):
            break;
        date_part = date_part + m
    

    if len(date_part.strip().split(" ")) > 1:
        sydney_time = datetime.strptime(date_part.strip(), "%H:%M %d/%m/%Y")
    else:
        sydney_time = datetime.strptime(date_part.strip(), "%d/%m/%Y")

    utc_time = sydney_to_utc(sydney_time)

    print("OrderNum: ", order_arr)
    print("Date and Time: ", utc_time)
    
def sydney_to_utc(sydney_time):
    local_tz = pytz.timezone('Australia/Sydney')
    sydney_time = local_tz.localize(sydney_time)
    target_tz = pytz.timezone('UTC')
    utc_time = target_tz.normalize(sydney_time)
    utc_time = utc_time.strftime("%Y-%m-%d %H:%M")

    return utc_time


if __name__ == "__main__":
    email_parse("Just to confirm your job: 1042079 23855 1042180 23856, has now been received in our warehouse. The date and time of the receive is: 09/05/2022 Free storage time finish at 23/05/2022")
    email_parse("Just to confirm your job: 20144 Alistair Reid 36 Augusta Street Glen Huntly VIC 3163 has now been Completed. The date and time of the job is: 10/05/2022")
    email_parse("Just to confirm your job: 20185 Tennis Victoria110/102 Olympic Boulevard Melbourne VIC 3000 has now been Rescheduled. The date and time of the job is: 8:00 16/05/2022 ")
    email_parse("Just to confirm your job: 20235 James Dugand Williams Corporation Level 6, 10 Queen street Melbourne VIC 3000 has now been Scheduled. The date and time of the job is: 7:00 11/05/2022")