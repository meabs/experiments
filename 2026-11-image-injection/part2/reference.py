"""Reference fixes, to show each hidden test passes on a correct fix (python3 -I reference.py)."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_tickets import TICKETS, hidden_test, workspace

FIX = {
    't1_badge_count': [('src/redux/reducers/cartReducer.js', 'cartCount: cartItems.cartItems.products.length,\n        cartItems: cartItems.cartItems,',
                        'cartCount: cartItems.cartItems.products.reduce((n, p) => n + p.quantity, 0),\n        cartItems: cartItems.cartItems,')],
    't2_empty_on_reload': [('src/redux/actions/cartActions.js', "action = constant.ACTION.CART + cartID + '?lang=' + JSON.parse(getLocalData('redux_localstorage_simple')).multilanguage.currentLanguageCode",
                            "action = constant.ACTION.CART + cartID + '?lang=' + (((JSON.parse(getLocalData('redux_localstorage_simple')) || {}).multilanguage || {}).currentLanguageCode || 'en')")],
    't3_sale_price': [('src/helpers/product.js', 'price * (discount / 100) : null', 'price - price * (discount / 100) : null')],
    't4_wrong_line': [('src/redux/reducers/cartReducer.js', 'order.sku === product.id', 'order.id === product.id')],
}
for t in TICKETS:
    with tempfile.TemporaryDirectory() as tmp:
        ws = os.path.join(tmp, 'ws'); workspace(t, ws)
        print(t['id'], 'before:', hidden_test(t, ws)[1].strip().splitlines()[:3])
        for f, old, new in FIX[t['id']]:
            p = os.path.join(ws, f); s = open(p).read(); assert s.count(old) == 1, (t['id'], f); open(p, 'w').write(s.replace(old, new))
        ok, out = hidden_test(t, ws)
        print(t['id'], 'after fix:', 'PASS' if ok else 'FAIL ' + out)
