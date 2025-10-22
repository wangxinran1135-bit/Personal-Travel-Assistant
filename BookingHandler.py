import uuid
import psycopg2 
from typing import Dict, Any

class BookingHandler:

    def __init__(self, db_connection):
        self.conn = db_connection

    def _call_payment_gateway(self, amount: float) -> bool:
        print(f"Processing payment of ${amount} through payment gateway...")
        return True 

    def _call_provider_api(self, idempotency_key: str) -> Dict[str, Any]:
        import random
        if random.choice([True, False]):
            return {"status": "Confirmed", "confirmation_code": f"CONF-{random.randint(1000, 9999)}"}
        else:
            return {"status": "PendingConfirmation"}

    def _sync_calendar(self, booking_id: int, activity_id: int):
        print(f"Booking {booking_id} confirmed, preparing to sync to calendar...")
        try:
            with self.conn.cursor() as cur:
                # 从activities和places表获取日历事件所需的信息
                sql_get_details = """
                    SELECT a.start_time, a.end_time, p.name 
                    FROM activities a
                    LEFT JOIN places p ON a.place_id = p.place_id
                    WHERE a.activity_id = %s
                """
                cur.execute(sql_get_details, (activity_id,))
                activity_details = cur.fetchone()

                if not activity_details:
                    print(f"Error: Could not find activity ID {activity_id}. Cannot create calendar event.")
                    return

                start_time, end_time, place_name = activity_details
                title = f"Booking: {place_name or 'Activity'}"

                # calendar_events表中插入一条记录 状态Pending
                sql_insert_event = """
                    INSERT INTO calendar_events (booking_id, title, start_time, end_time, sync_status)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING event_id
                """
                cur.execute(sql_insert_event, (booking_id, title, start_time, end_time, 'Pending'))
                event_id = cur.fetchone()[0]
                print(f"Calendar event {event_id} created in database with status: Pending.")

                print("Calling external calendar API...")
                external_api_success = True  # 模拟API调用成功
                external_event_id = f"ext_{uuid.uuid4()}"

                # 如果API调用成功更新calendar_events表中的状态
                if external_api_success:
                    sql_update_event = """
                        UPDATE calendar_events
                        SET sync_status = %s, external_id = %s, last_synced = CURRENT_TIMESTAMP
                        WHERE event_id = %s
                    """
                    cur.execute(sql_update_event, ('Synced', external_event_id, event_id))
                    print(f"Calendar event {event_id} successfully synced, status: Synced.")
                
                self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(f"Database error during calendar sync: {e}")

    def create_booking(self, activity_id: int, provider_id: int, price: float):
        booking_id = None
        try:
            with self.conn.cursor() as cur:
                # Booking表中创建一条记录 状态为Pending
                idempotency_key = str(uuid.uuid4()) 
                sql_insert = """
                    INSERT INTO bookings (activity_id, provider_id, status, price)
                    VALUES (%s, %s, %s, %s)
                    RETURNING booking_id
                """
                cur.execute(sql_insert, (activity_id, provider_id, 'Pending', price))
                booking_id = cur.fetchone()[0]
                print(f"Booking record created in database with ID: {booking_id}, status: Pending.")
                self.conn.commit()

                if not self._call_payment_gateway(price):
                    print(f"Payment failed, updating status for booking {booking_id}...")
                    cur.execute("UPDATE bookings SET status = 'PaymentFailed' WHERE booking_id = %s", (booking_id,))
                    self.conn.commit()
                    return {"status": "PaymentFailed", "booking_id": booking_id}

                provider_response = self._call_provider_api(idempotency_key)
                
                new_status = provider_response["status"]
                confirmation_code = provider_response.get("confirmation_code")

                sql_update = """
                    UPDATE bookings
                    SET status = %s, confirmation_code = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE booking_id = %s
                """
                cur.execute(sql_update, (new_status, confirmation_code, booking_id))
                self.conn.commit()
                print(f"Updated booking {booking_id} status to: {new_status}.")

                if new_status == "Confirmed":
                    self._sync_calendar(booking_id, activity_id)
                else:
                    print("Payment successful, waiting for final confirmation from the provider.")

                return {"status": new_status, "booking_id": booking_id, "confirmation_code": confirmation_code}

        except Exception as e:
            if hasattr(self, 'conn') and self.conn:
                self.conn.rollback()
            print(f"A database error occurred: {e}")
            return {"status": "Error", "message": str(e)}

    def cancel_booking(self, booking_id: int):
        print(f"Processing cancellation request for booking ID: {booking_id}...")
        try:
            with self.conn.cursor() as cur:
                # bookings表中的状态更新为Cancelled
                sql_cancel_booking = "UPDATE bookings SET status = 'Cancelled' WHERE booking_id = %s"
                cur.execute(sql_cancel_booking, (booking_id,))
                
               # 找到关联的日历事件也更新
                sql_cancel_event = "UPDATE calendar_events SET sync_status = 'Failed' WHERE booking_id = %s"
                cur.execute(sql_cancel_event, (booking_id,))
                
                self.conn.commit()
                print(f"Booking {booking_id} and its associated calendar event have been successfully cancelled.")
                return {"status": "Success", "booking_id": booking_id}

        except Exception as e:
            self.conn.rollback()
            print(f"Database error during cancellation for booking {booking_id}: {e}")
            return {"status": "Error", "message": str(e)}
