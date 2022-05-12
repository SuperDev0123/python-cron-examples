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

    order_arr = order_result.split(' ')
    # new_result = re.findall('[0-9]+', order_extract_str)
    date_extract_str = in_str[date_index + len(pre_date_str):]
    index = 0
    for m in date_extract_str:
        if m.isdigit():
            break
        index = index + 1
    
    date_result = date_extract_str[index:].split(' ')[0]
            
    print("OrderNum: ", order_arr)
    print("Date and Time: ", date_result)

if __name__ == "__main__":
    email_parse("Just to confirm your job: 1042079 23855 1042180 23856, has now been received in our warehouse. The date and time of the receive is: 09/05/2022 Free storage time finish at 23/05/2022")

# i.e: Just to confirm your job: 20144 Alistair Reid 36 Augusta Street Glen Huntly VIC 3163 has now been Completed. The date and time of the job is: 10/05/202