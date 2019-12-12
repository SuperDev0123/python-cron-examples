CREATE DEFINER=`fmadmin`@`%` PROCEDURE `MoveSuccess2ToBookings`()
BEGIN

DECLARE v_b_bookingID_Visual int(11);
DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
    GET DIAGNOSTICS CONDITION 1
    @p1 = RETURNED_SQLSTATE, @p2 = MESSAGE_TEXT;
    SELECT @p1 AS RETURNED_SQLSTATE, @p2 AS MESSAGE_TEXT;
        ROLLBACK;
    END;

START TRANSACTION;

SELECT max(b_bookingID_Visual) into v_b_bookingID_Visual FROM dme_bookings;

If (v_b_bookingID_Visual is NULL ) THEN
    SET v_b_bookingID_Visual := 89600;
END If;

SELECT 'Starting with Visual Id ' + v_b_bookingID_Visual;

INSERT INTO `dme_bookings` 
    (`pk_booking_id`, `b_clientReference_RA_Numbers`, `DME_price_from_client`, 
    `total_lines_qty_override`, `vx_freight_provider`, `v_vehicle_Type`, 
    `booking_Created_For`, `booking_Created_For_Email`, `x_ReadyStatus`, 
    `b_booking_Priority`, `b_handling_Instructions`, `pu_PickUp_Instructions_Contact`, 
    `pu_pickup_instructions_address`, `pu_WareHouse_Number`, `pu_WareHouse_Bay`, 
    `b_booking_tail_lift_pickup`, `b_booking_no_operator_pickup`, `puPickUpAvailFrom_Date`, 
    `pu_PickUp_Avail_Time_Hours`, `pu_PickUp_Avail_Time_Minutes`, `pu_PickUp_By_Date_DME`, 
    `pu_PickUp_By_Time_Hours_DME`, `pu_PickUp_By_Time_Minutes_DME`, `pu_Address_Type`, 
    `pu_Address_Street_1`, `pu_Address_street_2`, `pu_Address_State`, 
    `pu_Address_Suburb`, `pu_Address_PostalCode`, `pu_Address_Country`, 
    `pu_Contact_F_L_Name`, `pu_email_Group`, `pu_Phone_Main`, 
    `pu_Comm_Booking_Communicate_Via`, `de_to_addressed_Saved`, `b_booking_tail_lift_deliver`, 
    `b_bookingNoOperatorDeliver`, `de_to_Pick_Up_Instructions_Contact`, `de_to_PickUp_Instructions_Address`, 
    `de_to_WareHouse_Bay`, `de_to_WareHouse_Number`, `de_Deliver_From_Date`, 
    `de_Deliver_From_Hours`, `de_Deliver_From_Minutes`, `de_Deliver_By_Date`, 
    `de_Deliver_By_Hours`, `de_Deliver_By_Minutes`, `de_To_AddressType`, 
    `deToCompanyName`, `de_To_Address_Street_1`, `de_To_Address_Street_2`, 
    `de_To_Address_State`, `de_To_Address_Suburb`, `de_To_Address_PostalCode`, 
    `de_To_Address_Country`, `de_to_Contact_F_LName`, `de_Email_Group_Emails`, 
    `de_to_Phone_Main`, `de_to_Phone_Mobile`, `de_To_Comm_Delivery_Communicate_Via`, 
    `total_1_KG_weight_override`, `zb_002_client_booking_key`, `z_CreatedTimestamp`, 
    `b_bookingID_Visual`, `fk_client_warehouse_id`, `kf_client_id`, 
    `vx_serviceName`, `b_booking_Category`, `b_booking_Notes`, 
    `puCompany`, `pu_Email`, `pu_Phone_Mobile`, 
    `de_Email`, `v_service_Type`, `v_FPBookingNumber`,
    `b_status`, `b_client_booking_ref_num`, `b_client_del_note_num`,
    `b_client_order_num`, `b_client_sales_inv_num`, `b_client_warehouse_code`,
    `b_client_name`, `delivery_kpi_days`, `z_api_issue_update_flag_500`, `x_manual_booked_flag`)
SELECT bok_1.pk_header_id, bok_1.b_000_1_b_clientReference_RA_Numbers, b_000_2_b_price,
    bok_1.b_000_b_total_lines, bok_1.b_001_b_freight_provider, b_002_b_vehicle_type,
    bok_1.b_005_b_created_for, bok_1.b_006_b_created_for_email, b_007_b_ready_status,
    bok_1.b_009_b_priority, bok_1.b_014_b_pu_handling_instructions, b_015_b_pu_instructions_contact,
    bok_1.b_016_b_pu_instructions_address, bok_1.b_017_b_pu_warehouse_num, b_018_b_pu_warehouse_bay,
    bok_1.b_019_b_pu_tail_lift, bok_1.b_020_b_pu_num_operators, b_021_b_pu_avail_from_date,
    bok_1.b_022_b_pu_avail_from_time_hour, bok_1.b_023_b_pu_avail_from_time_minute, b_024_b_pu_by_date,
    bok_1.b_025_b_pu_by_time_hour, bok_1.b_026_b_pu_by_time_minute, b_027_b_pu_address_type,
    bok_1.b_029_b_pu_address_street_1, bok_1.b_030_b_pu_address_street_2, b_031_b_pu_address_state,
    bok_1.b_032_b_pu_address_suburb, bok_1.b_033_b_pu_address_postalcode, b_034_b_pu_address_country,
    bok_1.b_035_b_pu_contact_full_name, bok_1.b_036_b_pu_email_group, b_038_b_pu_phone_main,
    bok_1.b_040_b_pu_communicate_via, bok_1.pu_addressed_saved, b_041_b_del_tail_lift,
    bok_1.b_042_b_del_num_operators, b_043_b_del_instructions_contact, b_044_b_del_instructions_address,
    bok_1.b_045_b_del_warehouse_bay, b_046_b_del_warehouse_number, b_047_b_del_avail_from_date,
    bok_1.b_048_b_del_avail_from_time_hour, b_049_b_del_avail_from_time_minute, b_050_b_del_by_date,
    bok_1.b_051_b_del_by_time_hour, b_052_b_del_by_time_minute, b_053_b_del_address_type,
    bok_1.b_054_b_del_company, b_055_b_del_address_street_1, b_056_b_del_address_street_2,
    bok_1.b_057_b_del_address_state, b_058_b_del_address_suburb, b_059_b_del_address_postalcode,
    bok_1.b_060_b_del_address_country, b_061_b_del_contact_full_name, b_062_b_del_email_group,
    bok_1.b_064_b_del_phone_main, b_065_b_del_phone_mobile, b_066_b_del_communicate_via,
    bok_1.total_kg, v_client_pk_consigment_num, bok_1.z_createdTimeStamp,
    @a:=@a+1, bok_1.fk_client_warehouse_id, fk_client_id,
    bok_1.b_003_b_service_name, b_008_b_category, b_010_b_notes,
    bok_1.b_028_b_pu_company, b_037_b_pu_email, b_039_b_pu_phone_mobile,
    bok_1.b_063_b_del_email, vx_serviceType_XXX, bok_1.b_000_3_consignment_number,
    CASE 
        WHEN success = 2
            AND bok_1.b_000_3_consignment_number IS NOT NULL 
            AND bok_1.b_000_3_consignment_number <> "" 
            THEN 'Booked'
        WHEN success = 2 
            AND (bok_1.b_000_3_consignment_number IS NULL OR bok_1.b_000_3_consignment_number = "") 
            THEN 'Ready for booking'
        WHEN success = 3 
            THEN 'Ready for XML'
        WHEN success= 4 
            THEN 'Ready for CSV'
    END,
    bok_1.z_test, b_client_del_note_num,
    b_client_order_num, b_client_sales_inv_num, b_client_warehouse_code,
    dme_clients.company_name , IFNULL(delivery_days, 14),
    CASE WHEN success = 2 THEN 1 WHEN success = 3 THEN 0 WHEN success= 4 THEN 0 END,
    CASE WHEN success = 6 THEN 1 ELSE 0 END
FROM bok_1_headers bok_1
LEFT OUTER JOIN dme_clients ON fk_client_id=dme_account_num
LEFT OUTER JOIN utl_fp_delivery_times ON (b_001_b_freight_provider = fp_name AND cast(b_059_b_del_address_postalcode AS UNSIGNED) 
BETWEEN postal_code_from AND postal_code_to), (SELECT @a:= v_b_bookingID_Visual) AS a 
WHERE success IN (2,3,4,6);

SELECT 'Rows moved to dme_bookings = ' + ROW_COUNT();

UPDATE bok_1_headers SET success=1
WHERE success IN (2,3,4,6);


SELECT 'Starting move of booking lines';

INSERT INTO dme_booking_lines
    (e_spec_clientRMA_Number, e_weightPerEach,
    e_1_Total_dimCubicMeter, e_Total_KG_weight,
    e_item, e_qty,
    e_item_type, e_pallet_Type, fk_booking_id,
    e_dimLength, e_dimWidth, e_dimHeight,
    e_weightUOM, z_createdTimeStamp, e_dimUOM,
    client_item_reference, pk_booking_lines_id)
SELECT client_booking_id, l_009_weight_per_each,
    CASE
        WHEN upper(l_004_dim_UOM) = "CM"
            THEN l_002_qty * (l_005_dim_length * l_006_dim_width * l_007_dim_height / 1000000)
        WHEN upper( l_004_dim_UOM) IN ( "METER", "M")
            THEN (l_002_qty * l_005_dim_length * l_006_dim_width * l_007_dim_height)
        ELSE l_002_qty * (l_005_dim_length * l_006_dim_width * l_007_dim_height / 1000000000)
    END,
    CASE 
        WHEN lower(l_008_weight_UOM) IN ("g", "gram", "grams")
            THEN l_002_qty * l_009_weight_per_each / 1000
        WHEN lower(l_008_weight_UOM) IN ("kilogram", "kilograms", "kg", "kgs")
            THEN l_002_qty * l_009_weight_per_each 
        WHEN lower(l_008_weight_UOM) IN ("t", "ton", "tons")
            THEN l_002_qty * l_009_weight_per_each * 1000
        Else
            0
    END,
    l_003_item, l_002_qty,
    e_item_type, e_pallet_type, v_client_pk_consigment_num,
    l_005_dim_length, l_006_dim_width, l_007_dim_height,
    l_008_weight_UOM, z_createdTimeStamp, l_004_dim_UOM,
    client_item_reference, pk_booking_lines_id
FROM `bok_2_lines`
WHERE success IN (2,3,4,6);

SELECT 'Rows moved to dme_booking_lines = ' + ROW_COUNT();

UPDATE bok_2_lines SET success=1 WHERE success IN (2,3,4,6);


SELECT 'Starting move of booking lines data';

INSERT INTO dme_booking_lines_data 
    (pk_id_lines_data, fk_booking_id, quantity,
    modelNumber, itemDescription, itemFaultDescription,
    itemSerialNumbers, insuranceValueEach, gap_ra,
    clientRefNumber, z_createdByAccount, z_createdTimeStamp,
    z_modifiedByAccount, z_modifiedTimeStamp, fk_booking_lines_id)
SELECT pk_auto_id, v_client_pk_consigment_num, ld_001_qty,
    ld_002_model_number, ld_003_item_description, ld_004_fault_description,
    ld_005_item_serial_number, ld_006_insurance_value, ld_007_gap_ra,
    ld_008_client_ref_number, z_createdByAccount, z_createdTimeStamp,
    z_modifiedByAccount, z_modifiedTimeStamp, fk_booking_lines_id
FROM `bok_3_lines_data`
WHERE success IN (2,3,4,6);

SELECT 'Rows moved to dme_booking_lines_data = ' + ROW_COUNT();

UPDATE bok_3_lines_data SET success=1
WHERE success IN (2,3,4,6);

COMMIT;

END