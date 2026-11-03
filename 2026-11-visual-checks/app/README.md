# The storefront under test

okf-local's storefront (`~/code/benchmark/okf-local/fe`, Shopizer shop-react 3.0.0), copied unchanged and built
against the mock API:

    cp -r okf-local/fe app && cd app
    npm install --no-audit --no-fund --legacy-peer-deps --ignore-scripts   # the lock file is out of date
    sed -i 's|http://localhost:8080|http://localhost:8099|' env-config.js && cp env-config.js public/
    NODE_OPTIONS=--openssl-legacy-provider CI=false GENERATE_SOURCEMAP=false npx react-scripts build

`mock-api/serve.py` serves the build on port 3000 and the mock Shopizer API on 8099 from `mock-api/fixtures.json`
(store, two categories, six products, a three-item cart). It sets the cart cookie and the cookie-consent cookie, and
seeds the app's saved state with product 1 and the fixture cart, which a shopper would normally set by clicking. Node
22.22.1, react-scripts 4.0.3, Chrome headless for screenshots (`scripts/shoot.py`, all other hosts blocked).
