from app.applications import oxalis, oxalis_beater


register = oxalis.register(ack_always=True, reject=False)

@register
async def check():
    pass

oxalis_beater.register("*/1 * * * *", check)
