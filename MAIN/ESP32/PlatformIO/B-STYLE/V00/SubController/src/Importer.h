
#define B_STYLE (0)
/*Page Image Header*/
#if B_STYLE == (1)
#include "gfx/P0.h"
#else
#include "gfx/VELDO_P0.h"
#endif
#include "gfx/SUB.h"
#include "gfx/PBYE.h"

/*Seat Image Headers*/
/*Seat belt only*/
#include "gfx/S_P.h"
#include "gfx/W_P.h"
/*Passanger + Seat belt*/
#include "gfx/S_F.h"
#include "gfx/W_F.h"
/*Null Seat*/
#include "gfx/S_N.h"
#include "gfx/W_N.h"
/*Unregistred - Registred*/
#include "gfx/S_U.h"
#include "gfx/S_R.h"
#include "gfx/W_U.h"
#include "gfx/W_R.h"

/*Warning Image Headers*/

/*Error Image Headers*/
/*Battery Error GIF*/
#include "gfx/B_LOW.h"
#include "gfx/B_HIGH.h"

/*Information Image Headers*/
/*WI-FI*/
#include "gfx/WIFI_OFF.h"
#include "gfx/WIFI_1.h"
#include "gfx/WIFI_2.h"
#include "gfx/WIFI_3.h"
#include "gfx/WIFI_4.h"
/*GPS*/
#include "gfx/GPS_OFF.h"